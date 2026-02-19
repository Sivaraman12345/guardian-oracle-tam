// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ITWISOracle
 * @notice Interface for the Trophic-Web Integrity Score Oracle.
 *         Receives cryptographic proofs from the Guardian Oracle TAM
 *         edge node and makes verified TWIS scores available to
 *         insurance smart contracts.
 */
interface ITWISOracle {
    /// @notice Emitted when a new proof is submitted from the acoustic link.
    event ProofSubmitted(
        bytes32 indexed merkleRoot,
        uint256 twisScore,        // TWIS × 10000 (4 decimal fixed-point)
        uint256 leafCount,
        uint256 timestamp,
        address indexed submitter
    );

    /// @notice Emitted when TWIS drops below the insurance claim threshold.
    event ClaimTriggered(
        bytes32 indexed merkleRoot,
        uint256 twisScore,
        uint256 threshold,
        uint256 timestamp
    );

    /// @notice Submit a compact proof received via acoustic modem.
    /// @param merkleRoot The SHA-256 Merkle root hash of the sensor log batch.
    /// @param twisScore  The TWIS score as a fixed-point integer (× 10000).
    /// @param leafCount  Number of sensor log entries in the Merkle tree.
    function submitProof(
        bytes32 merkleRoot,
        uint256 twisScore,
        uint256 leafCount
    ) external;

    /// @notice Verify a full dataset against a previously committed Merkle root.
    /// @param merkleRoot The previously submitted root.
    /// @param dataHash   SHA-256 hash of the full dataset (optical dump).
    /// @return valid     True if the hashes match.
    function verifyFullDataset(
        bytes32 merkleRoot,
        bytes32 dataHash
    ) external view returns (bool valid);

    /// @notice Get the latest TWIS score.
    /// @return twisScore Fixed-point TWIS (× 10000).
    /// @return timestamp Block timestamp of the latest submission.
    function getLatestTWIS() external view returns (uint256 twisScore, uint256 timestamp);
}


/**
 * @title TWISOracle
 * @notice Implementation of the TWIS Oracle for insurance verification.
 *         Stores proofs submitted by the Guardian Oracle TAM and triggers
 *         insurance claims when TWIS falls below the configured threshold.
 */
contract TWISOracle is ITWISOracle {

    // ─── Storage ────────────────────────────────────────────────────

    struct Proof {
        uint256 twisScore;
        uint256 leafCount;
        uint256 timestamp;
        address submitter;
        bool    verified;       // True after full dataset verification
        bytes32 fullDataHash;   // Set during optical dump verification
    }

    /// @notice Mapping from Merkle root → stored proof.
    mapping(bytes32 => Proof) public proofs;

    /// @notice Ordered list of all submitted Merkle roots.
    bytes32[] public proofHistory;

    /// @notice TWIS threshold below which a claim is triggered (× 10000).
    uint256 public claimThreshold;

    /// @notice Address authorised to submit proofs (the edge node relay).
    address public authorizedSubmitter;

    /// @notice Contract owner.
    address public owner;

    // ─── Modifiers ──────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "TWISOracle: not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == authorizedSubmitter || msg.sender == owner,
            "TWISOracle: not authorized"
        );
        _;
    }

    // ─── Constructor ────────────────────────────────────────────────

    /**
     * @param _claimThreshold TWIS threshold (× 10000). E.g., 5000 = 0.5000.
     * @param _submitter      Address of the authorised edge-node relay.
     */
    constructor(uint256 _claimThreshold, address _submitter) {
        owner = msg.sender;
        claimThreshold = _claimThreshold;
        authorizedSubmitter = _submitter;
    }

    // ─── Core Functions ─────────────────────────────────────────────

    /// @inheritdoc ITWISOracle
    function submitProof(
        bytes32 merkleRoot,
        uint256 twisScore,
        uint256 leafCount
    ) external override onlyAuthorized {
        require(proofs[merkleRoot].timestamp == 0, "TWISOracle: proof already exists");

        proofs[merkleRoot] = Proof({
            twisScore:    twisScore,
            leafCount:    leafCount,
            timestamp:    block.timestamp,
            submitter:    msg.sender,
            verified:     false,
            fullDataHash: bytes32(0)
        });

        proofHistory.push(merkleRoot);

        emit ProofSubmitted(merkleRoot, twisScore, leafCount, block.timestamp, msg.sender);

        // Check claim trigger
        if (twisScore < claimThreshold) {
            emit ClaimTriggered(merkleRoot, twisScore, claimThreshold, block.timestamp);
        }
    }

    /// @inheritdoc ITWISOracle
    function verifyFullDataset(
        bytes32 merkleRoot,
        bytes32 dataHash
    ) external view override returns (bool valid) {
        Proof storage p = proofs[merkleRoot];
        require(p.timestamp > 0, "TWISOracle: proof not found");

        // In production, the full Merkle verification would happen here.
        // For the prototype, we check if the submitted data hash matches
        // the root (simplified verification).
        return merkleRoot == dataHash;
    }

    /// @inheritdoc ITWISOracle
    function getLatestTWIS() external view override returns (uint256 twisScore, uint256 timestamp) {
        require(proofHistory.length > 0, "TWISOracle: no proofs submitted");
        bytes32 latestRoot = proofHistory[proofHistory.length - 1];
        Proof storage p = proofs[latestRoot];
        return (p.twisScore, p.timestamp);
    }

    // ─── Admin Functions ────────────────────────────────────────────

    /// @notice Update the claim threshold.
    function setClaimThreshold(uint256 _threshold) external onlyOwner {
        claimThreshold = _threshold;
    }

    /// @notice Update the authorised submitter address.
    function setAuthorizedSubmitter(address _submitter) external onlyOwner {
        authorizedSubmitter = _submitter;
    }

    /// @notice Get the total number of proofs submitted.
    function proofCount() external view returns (uint256) {
        return proofHistory.length;
    }
}
