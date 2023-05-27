// main.js
var myAPIKey = process.env.GEOAPIFY_KEY;

// Use the API key to make a request
fetch(`https://api.geoapify.com/v1/geocode/search?text=New+York&apiKey=${myAPIKey}`)
  .then(response => response.json())
  .then(data => console.log(data));
