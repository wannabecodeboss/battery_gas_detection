import { initializeApp } 
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";

import { getDatabase, ref, get }
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";


/**********************
 Firebase Config
**********************/

const firebaseConfig = {

apiKey: "AIzaSyDXBV-8rXET5-OSKr6fG9FW3m6IVw1Ujsk",

databaseURL:
"https://battery-gas-detection-default-rtdb.asia-southeast1.firebasedatabase.app/"

};


const app = initializeApp(firebaseConfig);

const db = getDatabase(app);


/**********************
 Load Latest Session
**********************/

loadLatest();


async function loadLatest(){

document.getElementById("status").innerHTML =
"Loading latest session...";


const snapshot =
await get(ref(db,"/"));

const data = snapshot.val();


if(!data){

document.getElementById("status").innerHTML =
"No sessions found";

return;

}


/* Sort session names */

const sessions =
Object.keys(data).sort();


const latest =
sessions[sessions.length-1];


document.getElementById("status").innerHTML =

"Latest Session: " + latest;


/* Extract session */

const s = data[latest];


plot("h2oChart",s.timestamps,s.h2o,"H₂O");

plot("co2Chart",s.timestamps,s.co2,"CO₂");

plot("coChart",s.timestamps,s.co,"CO");

}



/**********************
 Plot Function
**********************/

function plot(id,timestamps,data,label){

/* Offset timestamps */

const t0 = timestamps[0];


/* Integer seconds */

const seconds = timestamps.map(
x => Math.floor(x - t0)
);


/* Convert to XY points */

const points = seconds.map((t,i)=>({

x: t,
y: data[i]

}));


new Chart(

document.getElementById(id),

{

type:'line',

data:{

datasets:[{

label:label,

data:points,

borderWidth:2,

pointRadius:0,

tension:0

}]

},

options:{

responsive:true,

maintainAspectRatio:false,

parsing:false,


plugins:{

legend:{
labels:{
color:'white'
}
}

},


scales:{

x:{

type:'linear',

ticks:{

color:'white',

stepSize:1,

precision:0,

callback: function(value){
return Math.floor(value);
}

},

title:{
display:true,
text:"Seconds",
color:'white'
}

},


y:{

ticks:{
color:'white'
},

title:{
display:true,
text:"ADC",
color:'white'
}

}

}

}

});

}
