//>>built
"undefined"===typeof Paho&&(Paho={});
Paho.MQTT=function(v){function y(a,b,c){b[c++]=a>>8;b[c++]=a%256;return c}function t(a,b,c,e){e=y(b,c,e);D(a,c,e);return e+b}function m(a){for(var b=0,c=0;c<a.length;c++){var e=a.charCodeAt(c);2047<e?(55296<=e&&56319>=e&&(c++,b++),b+=3):127<e?b+=2:b++}return b}function D(a,b,c){for(var e=0;e<a.length;e++){var d=a.charCodeAt(e);if(55296<=d&&56319>=d){var h=a.charCodeAt(++e);if(isNaN(h))throw Error(f(g.MALFORMED_UNICODE,[d,h]));d=(d-55296<<10)+(h-56320)+65536}127>=d?b[c++]=d:(2047>=d?b[c++]=d>>6&31|
192:(65535>=d?b[c++]=d>>12&15|224:(b[c++]=d>>18&7|240,b[c++]=d>>12&63|128),b[c++]=d>>6&63|128),b[c++]=d&63|128)}return b}function E(a,b,c){for(var e="",d,h=b;h<b+c;){d=a[h++];if(!(128>d)){var p=a[h++]-128;if(0>p)throw Error(f(g.MALFORMED_UTF,[d.toString(16),p.toString(16),""]));if(224>d)d=64*(d-192)+p;else{var u=a[h++]-128;if(0>u)throw Error(f(g.MALFORMED_UTF,[d.toString(16),p.toString(16),u.toString(16)]));if(240>d)d=4096*(d-224)+64*p+u;else{var l=a[h++]-128;if(0>l)throw Error(f(g.MALFORMED_UTF,
[d.toString(16),p.toString(16),u.toString(16),l.toString(16)]));if(248>d)d=262144*(d-240)+4096*p+64*u+l;else throw Error(f(g.MALFORMED_UTF,[d.toString(16),p.toString(16),u.toString(16),l.toString(16)]));}}}65535<d&&(d-=65536,e+=String.fromCharCode(55296+(d>>10)),d=56320+(d&1023));e+=String.fromCharCode(d)}return e}var z=function(a,b){for(var c in a)if(a.hasOwnProperty(c))if(b.hasOwnProperty(c)){if(typeof a[c]!==b[c])throw Error(f(g.INVALID_TYPE,[typeof a[c],c]));}else{a="Unknown property, "+c+". Valid properties are:";
for(c in b)b.hasOwnProperty(c)&&(a=a+" "+c);throw Error(a);}},q=function(a,b){return function(){return a.apply(b,arguments)}},g={OK:{code:0,text:"AMQJSC0000I OK."},CONNECT_TIMEOUT:{code:1,text:"AMQJSC0001E Connect timed out."},SUBSCRIBE_TIMEOUT:{code:2,text:"AMQJS0002E Subscribe timed out."},UNSUBSCRIBE_TIMEOUT:{code:3,text:"AMQJS0003E Unsubscribe timed out."},PING_TIMEOUT:{code:4,text:"AMQJS0004E Ping timed out."},INTERNAL_ERROR:{code:5,text:"AMQJS0005E Internal error. Error Message: {0}, Stack trace: {1}"},
CONNACK_RETURNCODE:{code:6,text:"AMQJS0006E Bad Connack return code:{0} {1}."},SOCKET_ERROR:{code:7,text:"AMQJS0007E Socket error:{0}."},SOCKET_CLOSE:{code:8,text:"AMQJS0008I Socket closed."},MALFORMED_UTF:{code:9,text:"AMQJS0009E Malformed UTF data:{0} {1} {2}."},UNSUPPORTED:{code:10,text:"AMQJS0010E {0} is not supported by this browser."},INVALID_STATE:{code:11,text:"AMQJS0011E Invalid state {0}."},INVALID_TYPE:{code:12,text:"AMQJS0012E Invalid type {0} for {1}."},INVALID_ARGUMENT:{code:13,text:"AMQJS0013E Invalid argument {0} for {1}."},
UNSUPPORTED_OPERATION:{code:14,text:"AMQJS0014E Unsupported operation."},INVALID_STORED_DATA:{code:15,text:"AMQJS0015E Invalid data in local storage key\x3d{0} value\x3d{1}."},INVALID_MQTT_MESSAGE_TYPE:{code:16,text:"AMQJS0016E Invalid MQTT message type {0}."},MALFORMED_UNICODE:{code:17,text:"AMQJS0017E Malformed Unicode string:{0} {1}."}},K={0:"Connection Accepted",1:"Connection Refused: unacceptable protocol version",2:"Connection Refused: identifier rejected",3:"Connection Refused: server unavailable",
4:"Connection Refused: bad user name or password",5:"Connection Refused: not authorized"},f=function(a,b){a=a.text;if(b)for(var c,e,d=0;d<b.length;d++)if(c="{"+d+"}",e=a.indexOf(c),0<e){var h=a.substring(0,e);a=a.substring(e+c.length);a=h+b[d]+a}return a},A=[0,6,77,81,73,115,100,112,3],B=[0,4,77,81,84,84,4],n=function(a,b){this.type=a;for(var c in b)b.hasOwnProperty(c)&&(this[c]=b[c])};n.prototype.encode=function(){var a=(this.type&15)<<4,b=0,c=[],e=0;void 0!=this.messageIdentifier&&(b+=2);switch(this.type){case 1:switch(this.mqttVersion){case 3:b+=
A.length+3;break;case 4:b+=B.length+3}b+=m(this.clientId)+2;if(void 0!=this.willMessage){b+=m(this.willMessage.destinationName)+2;var d=this.willMessage.payloadBytes;d instanceof Uint8Array||(d=new Uint8Array(g));b+=d.byteLength+2}void 0!=this.userName&&(b+=m(this.userName)+2);void 0!=this.password&&(b+=m(this.password)+2);break;case 8:a|=2;for(var h=0;h<this.topics.length;h++)c[h]=m(this.topics[h]),b+=c[h]+2;b+=this.requestedQos.length;break;case 10:a|=2;for(h=0;h<this.topics.length;h++)c[h]=m(this.topics[h]),
b+=c[h]+2;break;case 6:a|=2;break;case 3:this.payloadMessage.duplicate&&(a|=8);a=a|=this.payloadMessage.qos<<1;this.payloadMessage.retained&&(a|=1);e=m(this.payloadMessage.destinationName);var g=this.payloadMessage.payloadBytes;b=b+(e+2)+g.byteLength;g instanceof ArrayBuffer?g=new Uint8Array(g):g instanceof Uint8Array||(g=new Uint8Array(g.buffer))}var f=b;h=Array(1);var l=0;do{var r=f%128;f>>=7;0<f&&(r|=128);h[l++]=r}while(0<f&&4>l);f=h.length+1;b=new ArrayBuffer(b+f);l=new Uint8Array(b);l[0]=a;l.set(h,
1);if(3==this.type)f=t(this.payloadMessage.destinationName,e,l,f);else if(1==this.type){switch(this.mqttVersion){case 3:l.set(A,f);f+=A.length;break;case 4:l.set(B,f),f+=B.length}a=0;this.cleanSession&&(a=2);void 0!=this.willMessage&&(a=a|4|this.willMessage.qos<<3,this.willMessage.retained&&(a|=32));void 0!=this.userName&&(a|=128);void 0!=this.password&&(a|=64);l[f++]=a;f=y(this.keepAliveInterval,l,f)}void 0!=this.messageIdentifier&&(f=y(this.messageIdentifier,l,f));switch(this.type){case 1:f=t(this.clientId,
m(this.clientId),l,f);void 0!=this.willMessage&&(f=t(this.willMessage.destinationName,m(this.willMessage.destinationName),l,f),f=y(d.byteLength,l,f),l.set(d,f),f+=d.byteLength);void 0!=this.userName&&(f=t(this.userName,m(this.userName),l,f));void 0!=this.password&&t(this.password,m(this.password),l,f);break;case 3:l.set(g,f);break;case 8:for(h=0;h<this.topics.length;h++)f=t(this.topics[h],c[h],l,f),l[f++]=this.requestedQos[h];break;case 10:for(h=0;h<this.topics.length;h++)f=t(this.topics[h],c[h],
l,f)}return b};var F=function(a,b,c){this._client=a;this._window=b;this._keepAliveInterval=1E3*c;this.isReset=!1;var e=(new n(12)).encode(),d=function(a){return function(){return h.apply(a)}},h=function(){this.isReset?(this.isReset=!1,this._client._trace("Pinger.doPing","send PINGREQ"),this._client.socket.send(e),this.timeout=this._window.setTimeout(d(this),this._keepAliveInterval)):(this._client._trace("Pinger.doPing","Timed out"),this._client._disconnected(g.PING_TIMEOUT.code,f(g.PING_TIMEOUT)))};
this.reset=function(){this.isReset=!0;this._window.clearTimeout(this.timeout);0<this._keepAliveInterval&&(this.timeout=setTimeout(d(this),this._keepAliveInterval))};this.cancel=function(){this._window.clearTimeout(this.timeout)}},C=function(a,b,c,f,d){this._window=b;c||(c=30);this.timeout=setTimeout(function(a,b,c){return function(){return a.apply(b,c)}}(f,a,d),1E3*c);this.cancel=function(){this._window.clearTimeout(this.timeout)}},k=function(a,b,c,e,d){if(!("WebSocket"in v&&null!==v.WebSocket))throw Error(f(g.UNSUPPORTED,
["WebSocket"]));if(!("localStorage"in v&&null!==v.localStorage))throw Error(f(g.UNSUPPORTED,["localStorage"]));if(!("ArrayBuffer"in v&&null!==v.ArrayBuffer))throw Error(f(g.UNSUPPORTED,["ArrayBuffer"]));this._trace("Paho.MQTT.Client",a,b,c,e,d);this.host=b;this.port=c;this.path=e;this.uri=a;this.clientId=d;this._localKey=b+":"+c+("/mqtt"!=e?":"+e:"")+":"+d+":";this._msg_queue=[];this._sentMessages={};this._receivedMessages={};this._notify_msg_sent={};this._message_identifier=1;this._sequence=0;for(var h in localStorage)0!=
h.indexOf("Sent:"+this._localKey)&&0!=h.indexOf("Received:"+this._localKey)||this.restore(h)};k.prototype.host;k.prototype.port;k.prototype.path;k.prototype.uri;k.prototype.clientId;k.prototype.socket;k.prototype.connected=!1;k.prototype.maxMessageIdentifier=65536;k.prototype.connectOptions;k.prototype.hostIndex;k.prototype.onConnectionLost;k.prototype.onMessageDelivered;k.prototype.onMessageArrived;k.prototype.traceFunction;k.prototype._msg_queue=null;k.prototype._connectTimeout;k.prototype.sendPinger=
null;k.prototype.receivePinger=null;k.prototype.receiveBuffer=null;k.prototype._traceBuffer=null;k.prototype._MAX_TRACE_ENTRIES=100;k.prototype.connect=function(a){var b=this._traceMask(a,"password");this._trace("Client.connect",b,this.socket,this.connected);if(this.connected)throw Error(f(g.INVALID_STATE,["already connected"]));if(this.socket)throw Error(f(g.INVALID_STATE,["already connected"]));this.connectOptions=a;a.uris?(this.hostIndex=0,this._doConnect(a.uris[0])):this._doConnect(this.uri)};
k.prototype.subscribe=function(a,b){this._trace("Client.subscribe",a,b);if(!this.connected)throw Error(f(g.INVALID_STATE,["not connected"]));var c=new n(8);c.topics=[a];c.requestedQos=void 0!=b.qos?[b.qos]:[0];b.onSuccess&&(c.onSuccess=function(a){b.onSuccess({invocationContext:b.invocationContext,grantedQos:a})});b.onFailure&&(c.onFailure=function(a){b.onFailure({invocationContext:b.invocationContext,errorCode:a})});b.timeout&&(c.timeOut=new C(this,window,b.timeout,b.onFailure,[{invocationContext:b.invocationContext,
errorCode:g.SUBSCRIBE_TIMEOUT.code,errorMessage:f(g.SUBSCRIBE_TIMEOUT)}]));this._requires_ack(c);this._schedule_message(c)};k.prototype.unsubscribe=function(a,b){this._trace("Client.unsubscribe",a,b);if(!this.connected)throw Error(f(g.INVALID_STATE,["not connected"]));var c=new n(10);c.topics=[a];b.onSuccess&&(c.callback=function(){b.onSuccess({invocationContext:b.invocationContext})});b.timeout&&(c.timeOut=new C(this,window,b.timeout,b.onFailure,[{invocationContext:b.invocationContext,errorCode:g.UNSUBSCRIBE_TIMEOUT.code,
errorMessage:f(g.UNSUBSCRIBE_TIMEOUT)}]));this._requires_ack(c);this._schedule_message(c)};k.prototype.send=function(a){this._trace("Client.send",a);if(!this.connected)throw Error(f(g.INVALID_STATE,["not connected"]));wireMessage=new n(3);wireMessage.payloadMessage=a;0<a.qos?this._requires_ack(wireMessage):this.onMessageDelivered&&(this._notify_msg_sent[wireMessage]=this.onMessageDelivered(wireMessage.payloadMessage));this._schedule_message(wireMessage)};k.prototype.disconnect=function(){this._trace("Client.disconnect");
if(!this.socket)throw Error(f(g.INVALID_STATE,["not connecting or connected"]));wireMessage=new n(14);this._notify_msg_sent[wireMessage]=q(this._disconnected,this);this._schedule_message(wireMessage)};k.prototype.getTraceLog=function(){if(null!==this._traceBuffer){this._trace("Client.getTraceLog",new Date);this._trace("Client.getTraceLog in flight messages",this._sentMessages.length);for(var a in this._sentMessages)this._trace("_sentMessages ",a,this._sentMessages[a]);for(a in this._receivedMessages)this._trace("_receivedMessages ",
a,this._receivedMessages[a]);return this._traceBuffer}};k.prototype.startTrace=function(){null===this._traceBuffer&&(this._traceBuffer=[]);this._trace("Client.startTrace",new Date,"@VERSION@")};k.prototype.stopTrace=function(){delete this._traceBuffer};k.prototype._doConnect=function(a){this.connectOptions.useSSL&&(a=a.split(":"),a[0]="wss",a=a.join(":"));this.connected=!1;this.socket=4>this.connectOptions.mqttVersion?new WebSocket(a,["mqttv3.1"]):new WebSocket(a,["mqtt"]);this.socket.binaryType=
"arraybuffer";this.socket.onopen=q(this._on_socket_open,this);this.socket.onmessage=q(this._on_socket_message,this);this.socket.onerror=q(this._on_socket_error,this);this.socket.onclose=q(this._on_socket_close,this);this.sendPinger=new F(this,window,this.connectOptions.keepAliveInterval);this.receivePinger=new F(this,window,this.connectOptions.keepAliveInterval);this._connectTimeout=new C(this,window,this.connectOptions.timeout,this._disconnected,[g.CONNECT_TIMEOUT.code,f(g.CONNECT_TIMEOUT)])};k.prototype._schedule_message=
function(a){this._msg_queue.push(a);this.connected&&this._process_queue()};k.prototype.store=function(a,b){var c={type:b.type,messageIdentifier:b.messageIdentifier,version:1};switch(b.type){case 3:b.pubRecReceived&&(c.pubRecReceived=!0);c.payloadMessage={};for(var e="",d=b.payloadMessage.payloadBytes,h=0;h<d.length;h++)e=15>=d[h]?e+"0"+d[h].toString(16):e+d[h].toString(16);c.payloadMessage.payloadHex=e;c.payloadMessage.qos=b.payloadMessage.qos;c.payloadMessage.destinationName=b.payloadMessage.destinationName;
b.payloadMessage.duplicate&&(c.payloadMessage.duplicate=!0);b.payloadMessage.retained&&(c.payloadMessage.retained=!0);0==a.indexOf("Sent:")&&(void 0===b.sequence&&(b.sequence=++this._sequence),c.sequence=b.sequence);break;default:throw Error(f(g.INVALID_STORED_DATA,[key,c]));}localStorage.setItem(a+this._localKey+b.messageIdentifier,JSON.stringify(c))};k.prototype.restore=function(a){var b=localStorage.getItem(a),c=JSON.parse(b),e=new n(c.type,c);switch(c.type){case 3:b=c.payloadMessage.payloadHex;
var d=new ArrayBuffer(b.length/2);d=new Uint8Array(d);for(var h=0;2<=b.length;){var k=parseInt(b.substring(0,2),16);b=b.substring(2,b.length);d[h++]=k}b=new Paho.MQTT.Message(d);b.qos=c.payloadMessage.qos;b.destinationName=c.payloadMessage.destinationName;c.payloadMessage.duplicate&&(b.duplicate=!0);c.payloadMessage.retained&&(b.retained=!0);e.payloadMessage=b;break;default:throw Error(f(g.INVALID_STORED_DATA,[a,b]));}0==a.indexOf("Sent:"+this._localKey)?(e.payloadMessage.duplicate=!0,this._sentMessages[e.messageIdentifier]=
e):0==a.indexOf("Received:"+this._localKey)&&(this._receivedMessages[e.messageIdentifier]=e)};k.prototype._process_queue=function(){for(var a=null,b=this._msg_queue.reverse();a=b.pop();)this._socket_send(a),this._notify_msg_sent[a]&&(this._notify_msg_sent[a](),delete this._notify_msg_sent[a])};k.prototype._requires_ack=function(a){var b=Object.keys(this._sentMessages).length;if(b>this.maxMessageIdentifier)throw Error("Too many messages:"+b);for(;void 0!==this._sentMessages[this._message_identifier];)this._message_identifier++;
a.messageIdentifier=this._message_identifier;this._sentMessages[a.messageIdentifier]=a;3===a.type&&this.store("Sent:",a);this._message_identifier===this.maxMessageIdentifier&&(this._message_identifier=1)};k.prototype._on_socket_open=function(){var a=new n(1,this.connectOptions);a.clientId=this.clientId;this._socket_send(a)};k.prototype._on_socket_message=function(a){this._trace("Client._on_socket_message",a.data);this.receivePinger.reset();a=this._deframeMessages(a.data);for(var b=0;b<a.length;b+=
1)this._handleMessage(a[b])};k.prototype._deframeMessages=function(a){a=new Uint8Array(a);if(this.receiveBuffer){var b=new Uint8Array(this.receiveBuffer.length+a.length);b.set(this.receiveBuffer);b.set(a,this.receiveBuffer.length);a=b;delete this.receiveBuffer}try{b=0;for(var c=[];b<a.length;){a:{var e=a,d=b,h=d,k=e[d],u=k>>4,l=k&15;d+=1;var r=void 0,G=0,H=1;do{if(d==e.length){var m=[null,h];break a}r=e[d++];G+=(r&127)*H;H*=128}while(0!=(r&128));r=d+G;if(r>e.length)m=[null,h];else{var w=new n(u);
switch(u){case 2:e[d++]&1&&(w.sessionPresent=!0);w.returnCode=e[d++];break;case 3:h=l>>1&3;var t=256*e[d]+e[d+1];d+=2;var v=E(e,d,t);d+=t;0<h&&(w.messageIdentifier=256*e[d]+e[d+1],d+=2);var q=new Paho.MQTT.Message(e.subarray(d,r));1==(l&1)&&(q.retained=!0);8==(l&8)&&(q.duplicate=!0);q.qos=h;q.destinationName=v;w.payloadMessage=q;break;case 4:case 5:case 6:case 7:case 11:w.messageIdentifier=256*e[d]+e[d+1];break;case 9:w.messageIdentifier=256*e[d]+e[d+1],d+=2,w.returnCode=e.subarray(d,r)}m=[w,r]}}var x=
m[0];b=m[1];if(null!==x)c.push(x);else break}b<a.length&&(this.receiveBuffer=a.subarray(b))}catch(I){this._disconnected(g.INTERNAL_ERROR.code,f(g.INTERNAL_ERROR,[I.message,I.stack.toString()]));return}return c};k.prototype._handleMessage=function(a){this._trace("Client._handleMessage",a);try{switch(a.type){case 2:this._connectTimeout.cancel();if(this.connectOptions.cleanSession){for(var b in this._sentMessages){var c=this._sentMessages[b];localStorage.removeItem("Sent:"+this._localKey+c.messageIdentifier)}this._sentMessages=
{};for(b in this._receivedMessages){var e=this._receivedMessages[b];localStorage.removeItem("Received:"+this._localKey+e.messageIdentifier)}this._receivedMessages={}}if(0===a.returnCode)this.connected=!0,this.connectOptions.uris&&(this.hostIndex=this.connectOptions.uris.length);else{this._disconnected(g.CONNACK_RETURNCODE.code,f(g.CONNACK_RETURNCODE,[a.returnCode,K[a.returnCode]]));break}a=[];for(var d in this._sentMessages)this._sentMessages.hasOwnProperty(d)&&a.push(this._sentMessages[d]);a=a.sort(function(a,
b){return a.sequence-b.sequence});d=0;for(var h=a.length;d<h;d++)if(c=a[d],3==c.type&&c.pubRecReceived){var k=new n(6,{messageIdentifier:c.messageIdentifier});this._schedule_message(k)}else this._schedule_message(c);if(this.connectOptions.onSuccess)this.connectOptions.onSuccess({invocationContext:this.connectOptions.invocationContext});this._process_queue();break;case 3:this._receivePublish(a);break;case 4:if(c=this._sentMessages[a.messageIdentifier])if(delete this._sentMessages[a.messageIdentifier],
localStorage.removeItem("Sent:"+this._localKey+a.messageIdentifier),this.onMessageDelivered)this.onMessageDelivered(c.payloadMessage);break;case 5:if(c=this._sentMessages[a.messageIdentifier])c.pubRecReceived=!0,k=new n(6,{messageIdentifier:a.messageIdentifier}),this.store("Sent:",c),this._schedule_message(k);break;case 6:e=this._receivedMessages[a.messageIdentifier];localStorage.removeItem("Received:"+this._localKey+a.messageIdentifier);e&&(this._receiveMessage(e),delete this._receivedMessages[a.messageIdentifier]);
var m=new n(7,{messageIdentifier:a.messageIdentifier});this._schedule_message(m);break;case 7:c=this._sentMessages[a.messageIdentifier];delete this._sentMessages[a.messageIdentifier];localStorage.removeItem("Sent:"+this._localKey+a.messageIdentifier);if(this.onMessageDelivered)this.onMessageDelivered(c.payloadMessage);break;case 9:if(c=this._sentMessages[a.messageIdentifier]){c.timeOut&&c.timeOut.cancel();a.returnCode.indexOf=Array.prototype.indexOf;if(-1!==a.returnCode.indexOf(128)){if(c.onFailure)c.onFailure(a.returnCode)}else if(c.onSuccess)c.onSuccess(a.returnCode);
delete this._sentMessages[a.messageIdentifier]}break;case 11:if(c=this._sentMessages[a.messageIdentifier])c.timeOut&&c.timeOut.cancel(),c.callback&&c.callback(),delete this._sentMessages[a.messageIdentifier];break;case 13:this.sendPinger.reset();break;case 14:this._disconnected(g.INVALID_MQTT_MESSAGE_TYPE.code,f(g.INVALID_MQTT_MESSAGE_TYPE,[a.type]));break;default:this._disconnected(g.INVALID_MQTT_MESSAGE_TYPE.code,f(g.INVALID_MQTT_MESSAGE_TYPE,[a.type]))}}catch(l){this._disconnected(g.INTERNAL_ERROR.code,
f(g.INTERNAL_ERROR,[l.message,l.stack.toString()]))}};k.prototype._on_socket_error=function(a){this._disconnected(g.SOCKET_ERROR.code,f(g.SOCKET_ERROR,[a.data]))};k.prototype._on_socket_close=function(){this._disconnected(g.SOCKET_CLOSE.code,f(g.SOCKET_CLOSE))};k.prototype._socket_send=function(a){if(1==a.type){var b=this._traceMask(a,"password");this._trace("Client._socket_send",b)}else this._trace("Client._socket_send",a);this.socket.send(a.encode());this.sendPinger.reset()};k.prototype._receivePublish=
function(a){switch(a.payloadMessage.qos){case "undefined":case 0:this._receiveMessage(a);break;case 1:var b=new n(4,{messageIdentifier:a.messageIdentifier});this._schedule_message(b);this._receiveMessage(a);break;case 2:this._receivedMessages[a.messageIdentifier]=a;this.store("Received:",a);a=new n(5,{messageIdentifier:a.messageIdentifier});this._schedule_message(a);break;default:throw Error("Invaild qos\x3d"+wireMmessage.payloadMessage.qos);}};k.prototype._receiveMessage=function(a){if(this.onMessageArrived)this.onMessageArrived(a.payloadMessage)};
k.prototype._disconnected=function(a,b){this._trace("Client._disconnected",a,b);this.sendPinger.cancel();this.receivePinger.cancel();this._connectTimeout&&this._connectTimeout.cancel();this._msg_queue=[];this._notify_msg_sent={};this.socket&&(this.socket.onopen=null,this.socket.onmessage=null,this.socket.onerror=null,this.socket.onclose=null,1===this.socket.readyState&&this.socket.close(),delete this.socket);if(this.connectOptions.uris&&this.hostIndex<this.connectOptions.uris.length-1)this.hostIndex++,
this._doConnect(this.connectOptions.uris[this.hostIndex]);else if(void 0===a&&(a=g.OK.code,b=f(g.OK)),this.connected){if(this.connected=!1,this.onConnectionLost)this.onConnectionLost({errorCode:a,errorMessage:b})}else if(4===this.connectOptions.mqttVersion&&!1===this.connectOptions.mqttVersionExplicit)this._trace("Failed to connect V4, dropping back to V3"),this.connectOptions.mqttVersion=3,this.connectOptions.uris?(this.hostIndex=0,this._doConnect(this.connectOptions.uris[0])):this._doConnect(this.uri);
else if(this.connectOptions.onFailure)this.connectOptions.onFailure({invocationContext:this.connectOptions.invocationContext,errorCode:a,errorMessage:b})};k.prototype._trace=function(){if(this.traceFunction){for(var a in arguments)"undefined"!==typeof arguments[a]&&(arguments[a]=JSON.stringify(arguments[a]));a=Array.prototype.slice.call(arguments).join("");this.traceFunction({severity:"Debug",message:a})}if(null!==this._traceBuffer){a=0;for(var b=arguments.length;a<b;a++)this._traceBuffer.length==
this._MAX_TRACE_ENTRIES&&this._traceBuffer.shift(),0===a?this._traceBuffer.push(arguments[a]):"undefined"===typeof arguments[a]?this._traceBuffer.push(arguments[a]):this._traceBuffer.push("  "+JSON.stringify(arguments[a]))}};k.prototype._traceMask=function(a,b){var c={},f;for(f in a)a.hasOwnProperty(f)&&(c[f]=f==b?"******":a[f]);return c};var J=function(a,b,c,e){if("string"!==typeof a)throw Error(f(g.INVALID_TYPE,[typeof a,"host"]));if(2==arguments.length){e=b;var d=a;var h=d.match(/^(wss?):\/\/((\[(.+)\])|([^\/]+?))(:(\d+))?(\/.*)$/);
if(h)a=h[4]||h[2],b=parseInt(h[7]),c=h[8];else throw Error(f(g.INVALID_ARGUMENT,[a,"host"]));}else{3==arguments.length&&(e=c,c="/mqtt");if("number"!==typeof b||0>b)throw Error(f(g.INVALID_TYPE,[typeof b,"port"]));if("string"!==typeof c)throw Error(f(g.INVALID_TYPE,[typeof c,"path"]));d="ws://"+(-1!=a.indexOf(":")&&"["!=a.slice(0,1)&&"]"!=a.slice(-1)?"["+a+"]":a)+":"+b+c}for(var p=h=0;p<e.length;p++){var m=e.charCodeAt(p);55296<=m&&56319>=m&&p++;h++}if("string"!==typeof e||65535<h)throw Error(f(g.INVALID_ARGUMENT,
[e,"clientId"]));var l=new k(d,a,b,c,e);this._getHost=function(){return a};this._setHost=function(){throw Error(f(g.UNSUPPORTED_OPERATION));};this._getPort=function(){return b};this._setPort=function(){throw Error(f(g.UNSUPPORTED_OPERATION));};this._getPath=function(){return c};this._setPath=function(){throw Error(f(g.UNSUPPORTED_OPERATION));};this._getURI=function(){return d};this._setURI=function(){throw Error(f(g.UNSUPPORTED_OPERATION));};this._getClientId=function(){return l.clientId};this._setClientId=
function(){throw Error(f(g.UNSUPPORTED_OPERATION));};this._getOnConnectionLost=function(){return l.onConnectionLost};this._setOnConnectionLost=function(a){if("function"===typeof a)l.onConnectionLost=a;else throw Error(f(g.INVALID_TYPE,[typeof a,"onConnectionLost"]));};this._getOnMessageDelivered=function(){return l.onMessageDelivered};this._setOnMessageDelivered=function(a){if("function"===typeof a)l.onMessageDelivered=a;else throw Error(f(g.INVALID_TYPE,[typeof a,"onMessageDelivered"]));};this._getOnMessageArrived=
function(){return l.onMessageArrived};this._setOnMessageArrived=function(a){if("function"===typeof a)l.onMessageArrived=a;else throw Error(f(g.INVALID_TYPE,[typeof a,"onMessageArrived"]));};this._getTrace=function(){return l.traceFunction};this._setTrace=function(a){if("function"===typeof a)l.traceFunction=a;else throw Error(f(g.INVALID_TYPE,[typeof a,"onTrace"]));};this.connect=function(a){a=a||{};z(a,{timeout:"number",userName:"string",password:"string",willMessage:"object",keepAliveInterval:"number",
cleanSession:"boolean",useSSL:"boolean",invocationContext:"object",onSuccess:"function",onFailure:"function",hosts:"object",ports:"object",mqttVersion:"number"});void 0===a.keepAliveInterval&&(a.keepAliveInterval=60);if(4<a.mqttVersion||3>a.mqttVersion)throw Error(f(g.INVALID_ARGUMENT,[a.mqttVersion,"connectOptions.mqttVersion"]));void 0===a.mqttVersion?(a.mqttVersionExplicit=!1,a.mqttVersion=4):a.mqttVersionExplicit=!0;if(void 0===a.password&&void 0!==a.userName)throw Error(f(g.INVALID_ARGUMENT,
[a.password,"connectOptions.password"]));if(a.willMessage){if(!(a.willMessage instanceof x))throw Error(f(g.INVALID_TYPE,[a.willMessage,"connectOptions.willMessage"]));a.willMessage.stringPayload;if("undefined"===typeof a.willMessage.destinationName)throw Error(f(g.INVALID_TYPE,[typeof a.willMessage.destinationName,"connectOptions.willMessage.destinationName"]));}"undefined"===typeof a.cleanSession&&(a.cleanSession=!0);if(a.hosts){if(!(a.hosts instanceof Array))throw Error(f(g.INVALID_ARGUMENT,[a.hosts,
"connectOptions.hosts"]));if(1>a.hosts.length)throw Error(f(g.INVALID_ARGUMENT,[a.hosts,"connectOptions.hosts"]));for(var b=!1,e=0;e<a.hosts.length;e++){if("string"!==typeof a.hosts[e])throw Error(f(g.INVALID_TYPE,[typeof a.hosts[e],"connectOptions.hosts["+e+"]"]));if(/^(wss?):\/\/((\[(.+)\])|([^\/]+?))(:(\d+))?(\/.*)$/.test(a.hosts[e]))if(0==e)b=!0;else{if(!b)throw Error(f(g.INVALID_ARGUMENT,[a.hosts[e],"connectOptions.hosts["+e+"]"]));}else if(b)throw Error(f(g.INVALID_ARGUMENT,[a.hosts[e],"connectOptions.hosts["+
e+"]"]));}if(b)a.uris=a.hosts;else{if(!a.ports)throw Error(f(g.INVALID_ARGUMENT,[a.ports,"connectOptions.ports"]));if(!(a.ports instanceof Array))throw Error(f(g.INVALID_ARGUMENT,[a.ports,"connectOptions.ports"]));if(a.hosts.length!=a.ports.length)throw Error(f(g.INVALID_ARGUMENT,[a.ports,"connectOptions.ports"]));a.uris=[];for(e=0;e<a.hosts.length;e++){if("number"!==typeof a.ports[e]||0>a.ports[e])throw Error(f(g.INVALID_TYPE,[typeof a.ports[e],"connectOptions.ports["+e+"]"]));b=a.hosts[e];var h=
a.ports[e];d="ws://"+(-1!=b.indexOf(":")?"["+b+"]":b)+":"+h+c;a.uris.push(d)}}}l.connect(a)};this.subscribe=function(a,b){if("string"!==typeof a)throw Error("Invalid argument:"+a);b=b||{};z(b,{qos:"number",invocationContext:"object",onSuccess:"function",onFailure:"function",timeout:"number"});if(b.timeout&&!b.onFailure)throw Error("subscribeOptions.timeout specified with no onFailure callback.");if("undefined"!==typeof b.qos&&0!==b.qos&&1!==b.qos&&2!==b.qos)throw Error(f(g.INVALID_ARGUMENT,[b.qos,
"subscribeOptions.qos"]));l.subscribe(a,b)};this.unsubscribe=function(a,b){if("string"!==typeof a)throw Error("Invalid argument:"+a);b=b||{};z(b,{invocationContext:"object",onSuccess:"function",onFailure:"function",timeout:"number"});if(b.timeout&&!b.onFailure)throw Error("unsubscribeOptions.timeout specified with no onFailure callback.");l.unsubscribe(a,b)};this.send=function(a,b,c,d){if(0==arguments.length)throw Error("Invalid argument.length");if(1==arguments.length){if(!(a instanceof x)&&"string"!==
typeof a)throw Error("Invalid argument:"+typeof a);var e=a;if("undefined"===typeof e.destinationName)throw Error(f(g.INVALID_ARGUMENT,[e.destinationName,"Message.destinationName"]));}else e=new x(b),e.destinationName=a,3<=arguments.length&&(e.qos=c),4<=arguments.length&&(e.retained=d);l.send(e)};this.disconnect=function(){l.disconnect()};this.getTraceLog=function(){return l.getTraceLog()};this.startTrace=function(){l.startTrace()};this.stopTrace=function(){l.stopTrace()};this.isConnected=function(){return l.connected}};
J.prototype={get host(){return this._getHost()},set host(a){this._setHost(a)},get port(){return this._getPort()},set port(a){this._setPort(a)},get path(){return this._getPath()},set path(a){this._setPath(a)},get clientId(){return this._getClientId()},set clientId(a){this._setClientId(a)},get onConnectionLost(){return this._getOnConnectionLost()},set onConnectionLost(a){this._setOnConnectionLost(a)},get onMessageDelivered(){return this._getOnMessageDelivered()},set onMessageDelivered(a){this._setOnMessageDelivered(a)},
get onMessageArrived(){return this._getOnMessageArrived()},set onMessageArrived(a){this._setOnMessageArrived(a)},get trace(){return this._getTrace()},set trace(a){this._setTrace(a)}};var x=function(a){if("string"===typeof a||a instanceof ArrayBuffer||a instanceof Int8Array||a instanceof Uint8Array||a instanceof Int16Array||a instanceof Uint16Array||a instanceof Int32Array||a instanceof Uint32Array||a instanceof Float32Array||a instanceof Float64Array)var b=a;else throw f(g.INVALID_ARGUMENT,[a,"newPayload"]);
this._getPayloadString=function(){return"string"===typeof b?b:E(b,0,b.length)};this._getPayloadBytes=function(){if("string"===typeof b){var a=new ArrayBuffer(m(b));a=new Uint8Array(a);D(b,a,0);return a}return b};var c=void 0;this._getDestinationName=function(){return c};this._setDestinationName=function(a){if("string"===typeof a)c=a;else throw Error(f(g.INVALID_ARGUMENT,[a,"newDestinationName"]));};var e=0;this._getQos=function(){return e};this._setQos=function(a){if(0===a||1===a||2===a)e=a;else throw Error("Invalid argument:"+
a);};var d=!1;this._getRetained=function(){return d};this._setRetained=function(a){if("boolean"===typeof a)d=a;else throw Error(f(g.INVALID_ARGUMENT,[a,"newRetained"]));};var h=!1;this._getDuplicate=function(){return h};this._setDuplicate=function(a){h=a}};x.prototype={get payloadString(){return this._getPayloadString()},get payloadBytes(){return this._getPayloadBytes()},get destinationName(){return this._getDestinationName()},set destinationName(a){this._setDestinationName(a)},get qos(){return this._getQos()},
set qos(a){this._setQos(a)},get retained(){return this._getRetained()},set retained(a){this._setRetained(a)},get duplicate(){return this._getDuplicate()},set duplicate(a){this._setDuplicate(a)}};return{Client:J,Message:x}}(window);
//# sourceMappingURL=mqttws31.min.js.map