// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import {Test} from "forge-std/Test.sol";
import {FederatedHub} from "../src/FederatedHub.sol";

contract FederatedHubTest is Test {
    FederatedHub public hub;
    address public admin = address(0x1);
    address public alice = address(0x2);
    address public bob = address(0x3);

    function setUp() public {
        vm.prank(admin);
        hub = new FederatedHub();
    }

    function test_RegisterDID() public {
        vm.startPrank(alice);
        hub.registerDID("did:key:alice");
        
        (string memory did, bool isRegistered, bool isVerified) = hub.participants(alice);
        assertEq(did, "did:key:alice");
        assertTrue(isRegistered);
        assertFalse(isVerified);
        vm.stopPrank();
    }

    function test_VerifyParticipant() public {
        vm.prank(alice);
        hub.registerDID("did:key:alice");

        vm.prank(admin);
        hub.verifyParticipant(alice);

        (, , bool isVerified) = hub.participants(alice);
        assertTrue(isVerified);
    }
}
