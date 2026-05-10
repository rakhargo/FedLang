// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract FederatedHub {
    uint256 public projectCount;
    uint256 public constant MIN_CLIENTS = 3; // dev
    // uint256 public constant MAX_WAIT_TIME = 600; // 10 menit
    uint256 public constant TOTAL_CLIENTS = 5; // cuma buat dev
    uint256 public constant REWARD_PER_ROUND = 0.01 ether; // example
    uint256 public constant REWARD_PER_CONTRIBUTION_MIN = 0.001 ether; // example
    
    struct Project {
        address initiator;
        string globalModelCID;
        uint256 roundNumber;
        bool isActive;
        string name;           
        string description;    
        string modelName;
        uint256 totalBudget;      
    }

    struct Contribution {
        string modelUpdateCID;
        bytes32 contentHash;
        bytes signature;
        uint256 timestamp;
        bool exists;
    }

    struct Round {
        uint256 startTime;
        uint256 submissionCount;
        bool finalized;
    }

    struct Participant {
        string did; // Menyimpan identifier did:key:z6M...
        bool isRegistered;
    }

    mapping(address => Participant) public participants;
    mapping(uint256 => Project) public projects;
    mapping(address => uint256) public rewards; // saldo reward participants

    mapping(uint256 => mapping(address => bool)) public isRegistered;
    // ProjectId => RoundNumber => Participant => Contribution
    mapping(uint256 => mapping(uint256 => mapping(address => Contribution))) public contributions;
    // ProjectId => RoundNumber => RoundData
    mapping(uint256 => mapping(uint256 => Round)) public projectRounds;

    event ProjectCreated(uint256 indexed projectId, address indexed initiator, string initialCID);
    event ParticipantJoined(uint256 indexed projectId, address indexed participant);
    event ContributionSubmitted(uint256 indexed projectId, uint256 indexed round, address indexed participant);
    event RoundFinalized(uint256 indexed projectId, uint256 indexed round, string newGlobalCID);
    event ProjectFinalized(uint256 indexed projectId, uint256 finalRound, string finalModelCID);

    modifier onlyProjectInitiator(uint256 _projectId) {
        require(projects[_projectId].initiator == msg.sender, "Bukan inisiator proyek ini");
        _;
    }

    // Registrasi DID menggunakan format did:key (Algoritmik)
    function registerDID(string memory _did) public {
        participants[msg.sender].did = _did;
        participants[msg.sender].isRegistered = true;
    }

    function createProject(
        string memory _initialModelCID, 
        string memory _name, 
        string memory _description, 
        string memory _modelName
    ) public payable {
        require(participants[msg.sender].isRegistered, "Daftarkan DID Anda terlebih dahulu");
        // require(msg.value >= REWARD_PER_ROUND * 5, "Budget minimal 5 ronde"); // tunggu established

        projectCount++;
        projects[projectCount] = Project({
            initiator: msg.sender,
            globalModelCID: _initialModelCID,
            roundNumber: 1,
            isActive: true,
            name: _name,
            description: _description,
            modelName: _modelName,
            totalBudget: msg.value
        });

        projectRounds[projectCount][1].startTime = block.timestamp;
        emit ProjectCreated(projectCount, msg.sender, _initialModelCID);
    }

    function joinProject(uint256 _projectId) public {
        require(projects[_projectId].isActive, "Proyek tidak aktif");
        require(participants[msg.sender].isRegistered, "Daftarkan DID Anda terlebih dahulu");
        require(msg.sender != projects[_projectId].initiator, "Inisiator tidak boleh bergabung");
        require(!isRegistered[_projectId][msg.sender], "Sudah bergabung");
        
        isRegistered[_projectId][msg.sender] = true;
        emit ParticipantJoined(_projectId, msg.sender);
    }

    // Fungsi Submit dengan Signature untuk verifikasi identitas di sisi Aggregator
    function submitUpdate(
        uint256 _projectId, 
        string memory _modelUpdateCID, 
        bytes32 _contentHash,
        bytes memory _signature
    ) public {
        require(projects[_projectId].isActive, "Proyek sudah tidak aktif");
        require(isRegistered[_projectId][msg.sender], "Belum bergabung");
        
        uint256 curRound = projects[_projectId].roundNumber;
        require(!contributions[_projectId][curRound][msg.sender].exists, "Sudah submit di round ini");

        contributions[_projectId][curRound][msg.sender] = Contribution({
            modelUpdateCID: _modelUpdateCID,
            contentHash: _contentHash,
            signature: _signature,
            timestamp: block.timestamp,
            exists: true
        });

        projectRounds[_projectId][curRound].submissionCount++;
        emit ContributionSubmitted(_projectId, curRound, msg.sender);
    }

    // Mengecek apakah agregasi sudah boleh dilakukan
    function canAggregate(uint256 _projectId) public view returns (bool) {
        Project storage proj = projects[_projectId];
        Round storage r = projectRounds[_projectId][proj.roundNumber];
        
        // bool timeIsUp = block.timestamp >= r.startTime + MAX_WAIT_TIME;
        bool hasMinQuota = r.submissionCount >= MIN_CLIENTS;
        bool isFullHouse = r.submissionCount >= TOTAL_CLIENTS; // cuma buat dev

        // return isFullHouse || (hasMinQuota && timeIsUp); // 5 atau min quota dan time is up
        return isFullHouse || hasMinQuota;
    }

    function finalizeRound(
        uint256 _projectId, 
        string memory _newGlobalModelCID, 
        address[] memory _participants, 
        uint256[] memory _scores
    ) public onlyProjectInitiator(_projectId) {
        require(projects[_projectId].isActive, "Proyek tidak aktif");
        require(_participants.length == _scores.length, "Data tidak sinkron");
        require(canAggregate(_projectId), "Syarat agregasi belum terpenuhi");
        
        Project storage proj = projects[_projectId];
        uint256 finishedRound = proj.roundNumber;

        // Distribusi Reward
        for (uint256 i = 0; i < _participants.length; i++) {
            if (_scores[i] > 0) {
                // Skor 100 berarti dapat full porsi dari REWARD_PER_ROUND / jumlah partisipan
                // Atau bisa juga REWARD_PER_ROUND * score / 100 jika score adalah persentase performa
                uint256 participantReward = (REWARD_PER_ROUND * _scores[i]) / 100;
                rewards[_participants[i]] += participantReward;
            }
        }
        
        projectRounds[_projectId][finishedRound].finalized = true;
        proj.globalModelCID = _newGlobalModelCID;
        proj.roundNumber++;

        projectRounds[_projectId][proj.roundNumber].startTime = block.timestamp;
        emit RoundFinalized(_projectId, finishedRound, _newGlobalModelCID);
    }

    function withdrawRewards() public {
        uint256 amount = rewards[msg.sender];
        require(amount > 0, "Tidak ada saldo reward");
        rewards[msg.sender] = 0;
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer gagal");
    }

    function finalizeProject(uint256 _projectId) public onlyProjectInitiator(_projectId) {
        require(projects[_projectId].isActive, "Proyek sudah tidak aktif");
        
        projects[_projectId].isActive = false;
        
        emit ProjectFinalized(
            _projectId, 
            projects[_projectId].roundNumber, 
            projects[_projectId].globalModelCID
        );
    }
    
}