// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import {Script} from "forge-std/Script.sol";
import {FederatedHub} from "../src/FederatedHub.sol";

contract FederatedHubScript is Script {
    function setUp() public {}

    function run() public {
        vm.startBroadcast();
        new FederatedHub();
        vm.stopBroadcast();
    }
}
