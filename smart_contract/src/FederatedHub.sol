// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract FederatedHub {
    uint256 public projectCount;
    uint256 public constant MIN_CLIENTS = 3; // dev
    // uint256 public constant MAX_WAIT_TIME = 600; // 10 menit
    uint256 public constant TOTAL_CLIENTS = 5; // cuma buat dev
    
    struct Project {
        address initiator;
        string globalModelCID;
        uint256 roundNumber;
        bool isActive;
        string metadata; 
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
    mapping(uint256 => mapping(address => bool)) public isRegistered;
    // ProjectId => RoundNumber => Participant => Contribution
    mapping(uint256 => mapping(uint256 => mapping(address => Contribution))) public contributions;
    // ProjectId => RoundNumber => RoundData
    mapping(uint256 => mapping(uint256 => Round)) public projectRounds;

    event ProjectCreated(uint256 indexed projectId, address indexed initiator, string initialCID);
    event ParticipantJoined(uint256 indexed projectId, address indexed participant);
    event ContributionSubmitted(uint256 indexed projectId, uint256 indexed round, address indexed participant);
    event RoundFinalized(uint256 indexed projectId, uint256 indexed round, string newGlobalCID);

    modifier onlyProjectInitiator(uint256 _projectId) {
        require(projects[_projectId].initiator == msg.sender, "Bukan inisiator proyek ini");
        _;
    }

    // Registrasi DID menggunakan format did:key (Algoritmik)
    function registerDID(string memory _did) public {
        participants[msg.sender].did = _did;
        participants[msg.sender].isRegistered = true;
    }

    function createProject(string memory _initialModelCID, string memory _metadata) public {
        projectCount++;
        projects[projectCount] = Project({
            initiator: msg.sender,
            globalModelCID: _initialModelCID,
            roundNumber: 1,
            isActive: true,
            metadata: _metadata
        });

        // Inisialisasi waktu mulai untuk Round 1
        projectRounds[projectCount][1].startTime = block.timestamp;

        emit ProjectCreated(projectCount, msg.sender, _initialModelCID);
    }

    function joinProject(uint256 _projectId) public {
        require(projects[_projectId].isActive, "Proyek tidak aktif");
        // Tambahan: Partisipan harus sudah punya DID sebelum gabung project
        require(participants[msg.sender].isRegistered, "Daftarkan DID Anda terlebih dahulu");
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
        require(isRegistered[_projectId][msg.sender], "Belum bergabung");
        Project storage proj = projects[_projectId];
        uint256 curRound = proj.roundNumber;
        
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

    function finalizeRound(uint256 _projectId, string memory _newGlobalModelCID) public onlyProjectInitiator(_projectId) {
        require(canAggregate(_projectId), "Syarat agregasi belum terpenuhi");
        
        Project storage proj = projects[_projectId];
        uint256 finishedRound = proj.roundNumber;
        
        projectRounds[_projectId][finishedRound].finalized = true;
        
        proj.globalModelCID = _newGlobalModelCID;
        proj.roundNumber++;

        // Otomatis set waktu mulai untuk round berikutnya
        projectRounds[_projectId][proj.roundNumber].startTime = block.timestamp;
        emit RoundFinalized(_projectId, finishedRound, _newGlobalModelCID);
    }
}