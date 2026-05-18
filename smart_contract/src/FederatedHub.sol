// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract FederatedHub {
    address public platformAdmin; // Mewakili Tim FedLang selaku Deployer Platform
    mapping(string => address) public didToAddress; // Memastikan 1 DID hanya diklaim 1 wallet (Anti-Sybil)

    uint256 public projectCount;
    uint256 public constant MIN_CLIENTS = 3; // dev
    uint256 public constant TOTAL_CLIENTS = 5; // cuma buat dev
    uint256 public constant REWARD_PER_ROUND = 0.01 ether; // example
    
    struct Project {
        address initiator;
        string globalModelCID;
        uint256 roundNumber;
        bool isActive;
        string name;           
        string description;    
        string modelName;
        uint256 totalBudget;
        uint256 remainingBudget;      
    }

    struct Contribution {
        string modelUpdateCID; // Berisi CID JSON Metadata (Model CID + Berkas VC)
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
        bool isVerified; // TAMBAHAN: Status verifikasi global oleh Tim FedLang (Issuer Gate)
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
    event RefundSent(uint256 indexed projectId, address indexed initiator, uint256 amount);
    event DIDPlatformVerified(address indexed participant, string did);

    modifier onlyProjectInitiator(uint256 _projectId) {
        require(projects[_projectId].initiator == msg.sender, "Bukan inisiator proyek ini");
        _;
    }

    modifier onlyPlatformAdmin() {
        require(msg.sender == platformAdmin, "Hanya Tim FedLang yang dapat mengeksekusi ini");
        _;
    }

    // CONSTRUCTOR: Menetapkan Tim FedLang saat pertama kali deploy
    constructor() {
        platformAdmin = msg.sender;
    }

    function registerDID(string memory _did) public {
        require(bytes(_did).length > 0, "String DID tidak boleh kosong");
        require(!participants[msg.sender].isRegistered, "Wallet Anda sudah memiliki DID terdaftar");
        require(didToAddress[_did] == address(0), "DID ini sudah diklaim oleh wallet lain");

        participants[msg.sender].did = _did;
        participants[msg.sender].isRegistered = true;
        didToAddress[_did] = msg.sender; // Mengunci kepemilikan DID ke wallet pengirim (Anti-Sybil)
    }

    /**
     * @dev Berperan sebagai sistem penyaring eksternal. Tim FedLang memverifikasi 
     * profil partisipan secara off-chain dan memberikan validasi on-chain di tingkat platform.
     */
    function verifyParticipant(address _participant) public onlyPlatformAdmin {
        require(participants[_participant].isRegistered, "Partisipan belum mendaftarkan DID");
        require(!participants[_participant].isVerified, "Partisipan sudah terverifikasi");
        
        participants[_participant].isVerified = true;
        emit DIDPlatformVerified(_participant, participants[_participant].did);
    }

    function createProject(
        string memory _initialModelCID, 
        string memory _name, 
        string memory _description, 
        string memory _modelName
    ) public payable {
        require(participants[msg.sender].isRegistered, "Daftarkan DID Anda terlebih dahulu");
        require(participants[msg.sender].isVerified, "DID Anda belum diverifikasi oleh Tim FedLang"); // Proteksi Platform

        projectCount++;
        projects[projectCount] = Project({
            initiator: msg.sender,
            globalModelCID: _initialModelCID,
            roundNumber: 1,
            isActive: true,
            name: _name,
            description: _description,
            modelName: _modelName,
            totalBudget: msg.value,
            remainingBudget: msg.value
        });

        projectRounds[projectCount][1].startTime = block.timestamp;
        emit ProjectCreated(projectCount, msg.sender, _initialModelCID);
    }

    function joinProject(uint256 _projectId) public {
        require(projects[_projectId].isActive, "Proyek tidak aktif");
        require(participants[msg.sender].isRegistered, "Daftarkan DID Anda terlebih dahulu");
        require(participants[msg.sender].isVerified, "DID Anda belum diverifikasi oleh Tim FedLang"); // Proteksi Platform
        require(msg.sender != projects[_projectId].initiator, "Inisiator tidak boleh bergabung");
        require(!isRegistered[_projectId][msg.sender], "Sudah bergabung");
        
        isRegistered[_projectId][msg.sender] = true;
        emit ParticipantJoined(_projectId, msg.sender);
    }

    function submitUpdate(
        uint256 _projectId, 
        string memory _modelUpdateCID, // Diisi CID JSON Metadata (Mengandung tautan model & klaim VC)
        bytes32 _contentHash,
        bytes memory _signature
    ) public {
        require(projects[_projectId].isActive, "Proyek sudah tidak aktif");
        require(isRegistered[_projectId][msg.sender], "Belum bergabung");
        require(participants[msg.sender].isVerified, "Identitas platform Anda tidak valid"); // Proteksi Platform
        
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

    function canAggregate(uint256 _projectId) public view returns (bool) {
        Project storage proj = projects[_projectId];
        Round storage r = projectRounds[_projectId][proj.roundNumber];
        
        bool hasMinQuota = r.submissionCount >= MIN_CLIENTS;
        bool isFullHouse = r.submissionCount >= TOTAL_CLIENTS;

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
        uint256 totalRewardThisRound = 0;
        uint256 totalScoreInRound = 0;

        for (uint256 i = 0; i < _scores.length; i++) {
            totalScoreInRound += _scores[i];
        }

        for (uint256 i = 0; i < _participants.length; i++) {
            if (_scores[i] > 0) {
                uint256 participantReward = (REWARD_PER_ROUND * _scores[i]) / totalScoreInRound;
                totalRewardThisRound += participantReward;
                rewards[_participants[i]] += participantReward;
            }
        }
        
        require(proj.remainingBudget >= totalRewardThisRound, "Budget proyek tidak mencukupi!");
        proj.remainingBudget -= totalRewardThisRound;

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
        Project storage proj = projects[_projectId];
        require(proj.isActive, "Proyek sudah tidak aktif");

        uint256 refundAmount = proj.remainingBudget;
        proj.remainingBudget = 0;
        proj.isActive = false;
        
        if (refundAmount > 0) {
            (bool success, ) = payable(proj.initiator).call{value: refundAmount}("");
            require(success, "Refund gagal");
            emit RefundSent(_projectId, proj.initiator, refundAmount);
        }

        emit ProjectFinalized(_projectId, proj.roundNumber, proj.globalModelCID);
    }
}