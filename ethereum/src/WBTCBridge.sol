// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title WBTCBridge (ERC-721)
 * @notice Mint/burn logic for the BTC<>Ethereum bridge prototype.
 *
 * Peg-in:
 *   mint()       — operator signs LockTx txid → NFT minted to recipient
 *
 * Peg-out (TOOP):
 *   commitBurn() — burns the NFT immediately, publishes ek_C on-chain
 *                  so operators can send ephemeral keys off-chain
 *   submitGid()  — holder submits g_id on-chain after collecting operator keys
 *                  ChainVM verifies this against the Bitcoin SpendTx
 */
contract WBTCBridge is ERC721 {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    // -------------------------
    // State
    // -------------------------

    address public immutable operator;

    mapping(bytes32 => uint256) public instanceToToken;
    mapping(uint256 => bytes32) public tokenToInstance;
    mapping(bytes32 => bool) public minted;
    mapping(bytes32 => bool) public burned;
    mapping(bytes32 => address) public burner;  // instanceId → who called commitBurn

    uint256 private _nextTokenId;

    // -------------------------
    // Events
    // -------------------------

    event Minted(
        uint256 indexed tokenId,
        address indexed recipient,
        bytes32 indexed instanceId,
        bytes32 lockTxId
    );

    /// Token burned immediately — operators observe ek_C and send ephemeral keys
    event CommitBurned(
        address indexed burner,
        bytes32 indexed instanceId,
        bytes ekC
    );

    /// g_id committed on-chain for ChainVM verification on Bitcoin
    event GidSubmitted(
        address indexed submitter,
        bytes32 indexed instanceId,
        bytes32[] gId
    );

    // -------------------------
    // Constructor
    // -------------------------

    constructor(address _operator) ERC721("Wrapped BTC", "wBTC") {
        operator = _operator;
    }

    // -------------------------
    // Mint (peg-in)
    // -------------------------

    function mint(
        address recipient,
        bytes32 instanceId,
        bytes32 lockTxId,
        bytes calldata signature
    ) external {
        require(!minted[instanceId], "WBTCBridge: already minted");

        bytes32 msgHash = keccak256(abi.encodePacked(recipient, instanceId, lockTxId))
            .toEthSignedMessageHash();
        require(msgHash.recover(signature) == operator, "WBTCBridge: invalid operator signature");

        uint256 tokenId = _nextTokenId++;
        minted[instanceId] = true;
        instanceToToken[instanceId] = tokenId;
        tokenToInstance[tokenId] = instanceId;

        _safeMint(recipient, tokenId);
        emit Minted(tokenId, recipient, instanceId, lockTxId);
    }

    // -------------------------
    // CommitBurn (peg-out initiation)
    // -------------------------

    /**
     * @notice Burn the NFT and publish ek_C on-chain.
     *         Operators observe CommitBurned and send ephemeral keys to holder.
     */
    function commitBurn(uint256 tokenId, bytes calldata ekC) external {
        require(ownerOf(tokenId) == msg.sender, "WBTCBridge: not token owner");

        bytes32 instanceId = tokenToInstance[tokenId];
        burned[instanceId] = true;
        burner[instanceId] = msg.sender;

        _burn(tokenId);
        emit CommitBurned(msg.sender, instanceId, ekC);
    }

    // -------------------------
    // SubmitGid (peg-out completion)
    // -------------------------

    /**
     * @notice Submit g_id on-chain after collecting operator ephemeral keys.
     *         No token needed — just records g_id for ChainVM to verify.
     */
    function submitGid(bytes32 instanceId, bytes32[] calldata gId) external {
        require(burned[instanceId], "WBTCBridge: instance not burned");
        require(burner[instanceId] == msg.sender, "WBTCBridge: not the original burner");
        require(gId.length > 0, "WBTCBridge: g_id must be non-empty");

        emit GidSubmitted(msg.sender, instanceId, gId);
    }
}