// ==============================
// Firebase Imports
// ==============================

import { initializeApp } 
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";

import { getDatabase, ref, get }
from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";


// ==============================
// Firebase Config
// ==============================

const firebaseConfig = {
  apiKey: "AIzaSyDXBV-8rXET5-OSKr6fG9FW3m6IVw1Ujsk",
  databaseURL:
  "https://battery-gas-detection-default-rtdb.asia-southeast1.firebasedatabase.app/"
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);


// ==============================
// Load Latest Session
// ==============================

loadLatest();

async function loadLatest(){

try {

document.getElementById("status").innerHTML =
"Loading latest session...";

const snapshot = await get(ref(db,"/"));
const data = snapshot.val();

if(!data){
    document.getElementById("status").innerHTML =
    "No sessions found";
    return;
}

// Sort sessions
const sessions = Object.keys(data).sort();
const latest = sessions[sessions.length-1];

document.getElementById("status").innerHTML =
"Latest Session: " + latest;

const s = data[latest];

// 🔥 SAFE extraction (prevents crash)
const timestamps = s.timestamps || [];
const h2  = s.h2  || [];
const co2 = s.co2 || [];
const co  = s.co  || [];

// Debug log (very useful)
console.log("Session data:", s);

// Plot
plot("h2Chart", timestamps, h2, "H₂");
plot("co2Chart", timestamps, co2, "CO₂");
plot("coChart", timestamps, co, "CO");

} catch(e) {
    console.error("Load error:", e);
    document.getElementById("status").innerHTML =
    "Error loading data";
}

}


// ==============================
// Plot Function
// ==============================

function plot(id, timestamps, data, label){

// 🔴 Prevent crash
if (!timestamps || !data || timestamps.length === 0 || data.length === 0) {
    console.warn("Skipping plot:", label);
    return;
}

// 🔴 Ensure same length
const n = Math.min(timestamps.length, data.length);

// 🔥 Direct use (ESP timestamps already in seconds)
const points = [];

for(let i = 0; i < n; i++){
    points.push({
        x: timestamps[i],
        y: data[i]
    });
}

// Create chart
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
labels:{ color:'white' }
}
},

scales:{
x:{
type:'linear',
ticks:{ color:'white' },
title:{
display:true,
text:"Time (s)",
color:'white'
}
},

y:{
ticks:{ color:'white' },
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
