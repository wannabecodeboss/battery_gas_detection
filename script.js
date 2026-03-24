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
// GLOBAL CHART STORAGE
// ==============================

let charts = [];


// ==============================
// INIT (after DOM loads)
// ==============================

window.onload = () => {
    loadSessions();
};


// ==============================
// LOAD ALL SESSIONS
// ==============================

async function loadSessions(){

try {

document.getElementById("status").innerHTML =
"Loading sessions...";

const snapshot = await get(ref(db,"/"));
const data = snapshot.val();

if(!data){
    document.getElementById("status").innerHTML =
    "No sessions found";
    return;
}

// Sort sessions (latest last)
const sessions = Object.keys(data).sort();

const select = document.getElementById("sessionSelect");

// Clear dropdown
select.innerHTML = "";

// Populate dropdown
sessions.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    select.appendChild(opt);
});

// Default → latest
const latest = sessions[sessions.length - 1];
select.value = latest;

// Load latest session
loadSession(data, latest);

// Change handler
select.onchange = () => {
    loadSession(data, select.value);
};

document.getElementById("status").innerHTML =
"Loaded sessions";

} catch(e) {
    console.error("Load error:", e);
    document.getElementById("status").innerHTML =
    "Error loading sessions";
}

}


// ==============================
// LOAD SINGLE SESSION
// ==============================

function loadSession(data, sessionName){

const s = data[sessionName];

if(!s){
    console.error("Session not found:", sessionName);
    return;
}

document.getElementById("status").innerHTML =
"Viewing: " + sessionName;

// Safe extraction
const timestamps = s.timestamps || [];
const h2  = s.h2  || [];
const co2 = s.co2 || [];
const co  = s.co  || [];

console.log("Session data:", s);

// Clear previous charts
clearCharts();

// Plot
plot("h2Chart", timestamps, h2, "H₂");
plot("co2Chart", timestamps, co2, "CO₂");
plot("coChart", timestamps, co, "CO");

}


// ==============================
// CLEAR OLD CHARTS
// ==============================

function clearCharts(){
    charts.forEach(c => c.destroy());
    charts = [];
}


// ==============================
// PLOT FUNCTION
// ==============================

function plot(id, timestamps, data, label){

const canvas = document.getElementById(id);

// Validate canvas
if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
    console.error("Invalid canvas:", id);
    return;
}

// Prevent crashes
if (!timestamps || !data || timestamps.length === 0 || data.length === 0) {
    console.warn("Skipping plot:", label);
    return;
}

// Ensure equal length
const n = Math.min(timestamps.length, data.length);

// Build points
const points = [];

for(let i = 0; i < n; i++){
    points.push({
        x: timestamps[i],   // already in seconds from ESP
        y: data[i]
    });
}

// Create chart
const chart = new Chart(canvas, {

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

// Store chart reference
charts.push(chart);

}
