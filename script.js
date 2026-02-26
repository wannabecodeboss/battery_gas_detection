// Firebase config
const firebaseConfig = {

apiKey: "AIzaSyDXBV-8rXET5-OSKr6fG9FW3m6IVw1Ujsk",

databaseURL:
"https://battery-gas-detection-default-rtdb.asia-southeast1.firebasedatabase.app"

};

// Initialize Firebase

firebase.initializeApp(firebaseConfig);


const db = firebase.database();

const readingsRef = db.ref("readings");


// Chart

const ctx = document.getElementById("myChart");

let chart = new Chart(ctx, {

type: "line",

data: {

labels: [],

datasets: [

{

label: "Sensor Value",

data: [],

}

]

},

options: {

animation:false

}

});



// Live updates

readingsRef.on("value", function(snapshot){

let data = snapshot.val();

let labels = [];

let values = [];

for(let key in data){

labels.push(key);

values.push(data[key]);

}

chart.data.labels = labels;

chart.data.datasets[0].data = values;

chart.update();

});
