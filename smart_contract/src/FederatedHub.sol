// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

/**
 * @title FederatedHub
 * @dev Main contract for managing federated learning projects, participant registration, 
 * DID mappings, and rewarding client contributions based on training performance.
 */
contract FederatedHub {
    address public platformAdmin;
    
    // Maps each DID to its claiming wallet address to ensure 1-to-1 mapping
    mapping(string => address) public didToAddress; 

    uint256 public projectCount;
    uint256 public constant MIN_CLIENTS = 3; // Minimum clients required to aggregate (dev config)
    uint256 public constant TOTAL_CLIENTS = 5; // Total clients expected (dev config)
    uint256 public constant REWARD_PER_ROUND = 0.01 ether; // Standard reward distributed per round
    
    // Struct representing a Federated Learning Project
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
        uint256 participantCount; // Number of participants who have joined
    }

    // Struct representing a client's contribution for a round
    struct Contribution {
        string modelUpdateCID; // CID of JSON metadata containing model link & VC document
        bytes32 contentHash;
        bytes signature;
        uint256 timestamp;
        bool exists;
    }

    // Struct tracking data of each round
    struct Round {
        uint256 startTime;
        uint256 submissionCount;
        bool finalized;
    }

    // Struct storing participant DID and platform verification status
    struct Participant {
        string did; // Stores DID identifier (e.g. did:key:z6M...)
        bool isRegistered;
        bool isVerified; // Global verification status by the FedLang Team (Issuer Gate)
    }

    mapping(address => Participant) public participants;
    mapping(uint256 => Project) public projects;
    mapping(address => uint256) public rewards; // Reward balances for participants

    // Tracks if a participant is registered in a specific project
    mapping(uint256 => mapping(address => bool)) public isRegistered;
    
    // ProjectId => RoundNumber => Participant => Contribution
    mapping(uint256 => mapping(uint256 => mapping(address => Contribution))) public contributions;
    
    // ProjectId => RoundNumber => RoundData
    mapping(uint256 => mapping(uint256 => Round)) public projectRounds;

    // Events
    event ProjectCreated(uint256 indexed projectId, address indexed initiator, string initialCID);
    event ParticipantJoined(uint256 indexed projectId, address indexed participant);
    event ContributionSubmitted(uint256 indexed projectId, uint256 indexed round, address indexed participant);
    event RoundFinalized(uint256 indexed projectId, uint256 indexed round, string newGlobalCID);
    event ProjectFinalized(uint256 indexed projectId, uint256 finalRound, string finalModelCID);
    event RefundSent(uint256 indexed projectId, address indexed initiator, uint256 amount);
    event DIDPlatformVerified(address indexed participant, string did);

    modifier onlyProjectInitiator(uint256 _projectId) {
        require(projects[_projectId].initiator == msg.sender, "Not the project initiator");
        _;
    }

    modifier onlyPlatformAdmin() {
        require(msg.sender == platformAdmin, "Only the FedLang Team can execute this");
        _;
    }

    // CONSTRUCTOR: Sets the deployer as the platform admin
    constructor() {
        platformAdmin = msg.sender;
    }

    /**
     * @notice Registers a decentralized identifier (DID) for the sender's wallet
     * @param _did The DID string to register
     */
    function registerDID(string memory _did) public {
        require(bytes(_did).length > 0, "DID string cannot be empty");
        require(!participants[msg.sender].isRegistered, "Your wallet already has a registered DID");
        require(didToAddress[_did] == address(0), "This DID has already been claimed by another wallet");

        participants[msg.sender].did = _did;
        participants[msg.sender].isRegistered = true;
        didToAddress[_did] = msg.sender; // Locks DID ownership to sender's wallet (Anti-Sybil)
    }

    /**
     * @notice Verifies a participant on-chain after off-chain verification by admin
     * @dev Acts as an external screening system. The FedLang Team verifies 
     * participant profiles off-chain and provides on-chain validation at the platform level.
     * @param _participant The wallet address of the participant to verify
     */
    function verifyParticipant(address _participant) public onlyPlatformAdmin {
        require(participants[_participant].isRegistered, "Participant has not registered a DID");
        require(!participants[_participant].isVerified, "Participant is already verified");
        
        participants[_participant].isVerified = true;
        emit DIDPlatformVerified(_participant, participants[_participant].did);
    }

    /**
     * @notice Creates a new federated learning project with an initial global model
     */
    function createProject(
        string memory _initialModelCID, 
        string memory _name, 
        string memory _description, 
        string memory _modelName
    ) public payable {
        require(participants[msg.sender].isRegistered, "Please register your DID first");
        require(participants[msg.sender].isVerified, "Your DID has not been verified by the FedLang Team"); // Platform Protection

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
            remainingBudget: msg.value,
            participantCount: 0
        });

        projectRounds[projectCount][1].startTime = block.timestamp;
        emit ProjectCreated(projectCount, msg.sender, _initialModelCID);
    }

    /**
     * @notice Allows a verified participant to join an active project
     */
    function joinProject(uint256 _projectId) public {
        require(projects[_projectId].isActive, "Project is not active");
        require(participants[msg.sender].isRegistered, "Please register your DID first");
        require(participants[msg.sender].isVerified, "Your DID has not been verified by the FedLang Team"); // Platform Protection
        require(msg.sender != projects[_projectId].initiator, "Initiator is not allowed to join");
        require(!isRegistered[_projectId][msg.sender], "Already joined");
        
        isRegistered[_projectId][msg.sender] = true;
        projects[_projectId].participantCount++;
        emit ParticipantJoined(_projectId, msg.sender);
    }

    /**
     * @notice Submits a local model update contribution for the current round
     */
    function submitUpdate(
        uint256 _projectId, 
        string memory _modelUpdateCID, // Filled with JSON metadata CID (Contains model link & VC claims)
        bytes32 _contentHash,
        bytes memory _signature
    ) public {
        require(projects[_projectId].isActive, "Project is no longer active");
        require(isRegistered[_projectId][msg.sender], "Has not joined the project");
        require(participants[msg.sender].isVerified, "Your platform identity is invalid"); // Platform Protection
        
        uint256 curRound = projects[_projectId].roundNumber;
        require(!contributions[_projectId][curRound][msg.sender].exists, "Already submitted in this round");

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

    /**
     * @notice Checks if the project has enough submissions to start aggregation for the round
     */
    function canAggregate(uint256 _projectId) public view returns (bool) {
        Project storage proj = projects[_projectId];
        Round storage r = projectRounds[_projectId][proj.roundNumber];
        
        bool hasMinQuota = r.submissionCount >= MIN_CLIENTS;
        bool isFullHouse = r.submissionCount >= TOTAL_CLIENTS;

        return isFullHouse || hasMinQuota;
    }

    /**
     * @notice Finalizes the current round, aggregates models (off-chain), distributes rewards, and starts the next round
     */
    function finalizeRound(
        uint256 _projectId, 
        string memory _newGlobalModelCID, 
        address[] memory _participants, 
        uint256[] memory _scores
    ) public onlyProjectInitiator(_projectId) {
        require(projects[_projectId].isActive, "Project is not active");
        require(_participants.length == _scores.length, "Data is out of sync");
        require(canAggregate(_projectId), "Aggregation requirements are not met");
        
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
        
        require(proj.remainingBudget >= totalRewardThisRound, "Insufficient project budget!");
        proj.remainingBudget -= totalRewardThisRound;

        projectRounds[_projectId][finishedRound].finalized = true;
        proj.globalModelCID = _newGlobalModelCID;
        proj.roundNumber++;

        projectRounds[_projectId][proj.roundNumber].startTime = block.timestamp;
        emit RoundFinalized(_projectId, finishedRound, _newGlobalModelCID);
    }

    /**
     * @notice Withdraws the caller's earned reward balance
     */
    function withdrawRewards() public {
        uint256 amount = rewards[msg.sender];
        require(amount > 0, "No reward balance available");
        rewards[msg.sender] = 0;
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
    }

    /**
     * @notice Ends the project, marks it inactive, and refunds remaining budget to initiator
     */
    function finalizeProject(uint256 _projectId) public onlyProjectInitiator(_projectId) {
        Project storage proj = projects[_projectId];
        require(proj.isActive, "Project is no longer active");

        uint256 refundAmount = proj.remainingBudget;
        proj.remainingBudget = 0;
        proj.isActive = false;
        
        if (refundAmount > 0) {
            (bool success, ) = payable(proj.initiator).call{value: refundAmount}("");
            require(success, "Refund failed");
            emit RefundSent(_projectId, proj.initiator, refundAmount);
        }

        emit ProjectFinalized(_projectId, proj.roundNumber, proj.globalModelCID);
    }
}