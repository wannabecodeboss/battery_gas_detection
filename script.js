import { initializeApp }
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";

import {
getDatabase,
ref,
get
}
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";


const firebaseConfig = {

apiKey: "AIzaSyDXBV-8rXET5-OSKr6fG9FW3m6IVw1Ujsk",

databaseURL:
"https://battery-gas-detection-default-rtdb.asia-southeast1.firebasedatabase.app/"

};


const app=initializeApp(firebaseConfig);

const db=getDatabase(app);


loadLatest();


async function loadLatest(){

document.getElementById("status").innerHTML=
"Fetching sessions...";

const snapshot=
await get(ref(db,"/"));

const data=snapshot.val();


const sessions=
Object.keys(data).sort();


const latest=
sessions[sessions.length-1];


document.getElementById("status").innerHTML=

"Latest Session: "+latest;


const s=data[latest];


plot("h2oChart",s.timestamps,s.h2o,"H2O");

plot("co2Chart",s.timestamps,s.co2,"CO2");

plot("coChart",s.timestamps,s.co,"CO");

}



function plot(id,timestamps,data,label){

const t0=timestamps[0];

const time=timestamps.map(x=>x-t0);


new Chart(

document.getElementById(id),

{
type:'line',

data:{

labels:time,

datasets:[{

label:label,

data:data,

borderWidth:1,

pointRadius:0

}]

},

options:{

responsive:true,

maintainAspectRatio:false,

scales:{

x:{
title:{
display:true,
text:"Seconds"
}
},

y:{
title:{
display:true,
text:"ADC"
}
}

}

}

}

);

}
