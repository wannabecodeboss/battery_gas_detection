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
// WAIT FOR DOM (bulletproof)
// ==============================

document.addEventListener("DOMContentLoaded", () => {
    loadSessions();
});


// ==============================
// LOAD ALL SESSIONS
// ==============================

async function loadSessions(){

try {

const statusEl = document.getElementById("status");
const select = document.getElementById("sessionSelect");

// 🔴 Hard fail if UI missing
if (!select) {
    console.error("❌ sessionSelect dropdown not found in HTML");
    return;
}

if (statusEl)
    statusEl.innerHTML = "Loading sessions...";

const snapshot = await get(ref(db,"/"));
const data = snapshot.val();

// 🔍 DEBUG
console.log("Firebase root data:", data);

if(!data){
    if (statusEl)
        statusEl.innerHTML = "No sessions found";
    return;
}

// Sort sessions
const sessions = Object.keys(data).sort();

console.log("Sessions found:", sessions);

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

if (statusEl)
    statusEl.innerHTML = "Loaded sessions";

} catch(e) {
    console.error("❌ Load error:", e);

    const statusEl = document.getElementById("status");
    if (statusEl)
        statusEl.innerHTML = "Error loading sessions";
}

}


// ==============================
// LOAD SINGLE SESSION
// ==============================

function loadSession(data, sessionName){

const statusEl = document.getElementById("status");

const s = data[sessionName];

if(!s){
    console.error("Session not found:", sessionName);
    return;
}

if (statusEl)
    statusEl.innerHTML = "Viewing: " + sessionName;

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

// 🔴 Validate canvas
if (!canvas) {
    console.error("Canvas not found:", id);
    return;
}

if (!(canvas instanceof HTMLCanvasElement)) {
    console.error("Not a canvas:", id);
    return;
}

// 🔴 Prevent crash
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
        x: timestamps[i],   // already seconds from ESP
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
