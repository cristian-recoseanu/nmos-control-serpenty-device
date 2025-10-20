# nmos-control-serpenty-device

An example NMOS Device implementing [IS-12](https://specs.amwa.tv/is-12/).

## Get started

Install dependencies
```bash
pip install -r requirements.txt
```

Run
```bash
python main.py
```

## Working features

The following features are working:

* Hosting a basic [IS-04 node api](https://specs.amwa.tv/is-04/releases/v1.3.3/APIs/NodeAPI.html) with only node and device resources
* Advertising the IS-12 control endpoint (`urn:x-nmos:control:ncp/v1.0`) inside the [IS-04 device](https://specs.amwa.tv/is-12/releases/v1.0.1/docs/IS-04_interactions.html) resource
* Hosting a WebSocket server which the IS-12 endpoint uses for bidirectional communication
* Receiving Command messages and sending Command Response messages by pairing their handles ([IS-12 messages](https://specs.amwa.tv/is-12/releases/v1.0.1/docs/Protocol_messaging.html))
* Receiving Subscription messages and sending Notification messages whenever object properties change ([IS-12 schemas](https://specs.amwa.tv/is-12/releases/v1.0.1/APIs/schemas/))
* Offering a basic NcObject implementation
    * Implementing the generic Get method of any object to retrieve the value of any property ([NcObject](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/NcObject.html#generic-getter-and-setter))
    * Implementing the generic Set method of any object to set the value of any property ([NcObject](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/Framework.html#ncobject))
* Offering an NcBlock implementation and advertising a root block and nested block
    * Implementing all [NcBlock](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/Framework.html#ncblock) methods

## To do

The following features are planned:

* Implementing the [ClassManager](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/Framework.html#ncclassmanager)
    * Implementing [class discovery](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/Managers.html#class-manager)
    * Implementing [datatype discovery](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/Managers.html#class-manager)
* Implementing the [IS-04 registration workflow](https://specs.amwa.tv/is-04/releases/v1.3.3/APIs/RegistrationAPI.html) so we can register resources in an NMOS registry and maintain the registrations via heartbeats
* Implementing the [NcReceiverMonitor](https://specs.amwa.tv/nmos-control-feature-sets/branches/main/monitoring/#ncreceivermonitor) model
* Implementing the [NcSenderMonitor](https://specs.amwa.tv/nmos-control-feature-sets/branches/main/monitoring/#ncsendermonitor) model
* Implementing the [IS-05 connection management](https://specs.amwa.tv/is-05/releases/v1.1.2/APIs/ConnectionAPI.html) api with senders and receivers being monitored by associated sender and receiver monitors with appropriate [touchpoints](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/NcObject.html#touchpoints)
* Implementing the [BCP-008-01](https://specs.amwa.tv/bcp-008-01/) behaviour in regards to activation, status reporting delay, overall status mapping and transition counters
* Implementing the [BCP-008-02](https://specs.amwa.tv/bcp-008-02/) behaviour in regards to activation, status reporting delay, overall status mapping and transition counters
* Implementing a [vendor specific](https://specs.amwa.tv/ms-05-02/branches/v1.0.x/docs/Introduction.html) class

## Other useful resources

Here are other resources available around NMOS Control & Monitoring:

* A Rust counterpart to this repository (IS-12 device implementation)  
https://github.com/cristian-recoseanu/nmos-control-rusty-device

* An open source client/controller IS-12/BCP-008 example implementation in TypeScript/NodeJS  
https://github.com/cristian-recoseanu/nmos-control-scripty-client

* A comprehensive Implementers guide (INFO-006)  
https://specs.amwa.tv/info-006/

* The nmos-device-control-mock showcasing a fully compliant and tested implementation of IS-12 and BCP-008 in TypeScript/NodeJS  
https://github.com/AMWA-TV/nmos-device-control-mock

* nmos-cpp open source library with a fully compliant and tested implementation of IS-12 and BCP-008 in C++  
https://github.com/sony/nmos-cpp

* nmos-testing framework  
https://specs.amwa.tv/nmos-testing/
