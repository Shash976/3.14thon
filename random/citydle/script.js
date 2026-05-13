document.addEventListener("DOMContentLoaded", () => {
    const cityInput = document.getElementById("cityInput");
    const guessButton = document.getElementById("guessButton");
    const guessesContainer = document.querySelector(".guesses");
    let attempts = 0;

    guessButton.addEventListener("click", () => {
        const userGuess = cityInput.value.trim();
    
        if (userGuess) {
            const guessedCity = findCity(userGuess); // Replace with your city-finding logic
            if (guessedCity) {
                const distance = calculateDistance(
                    targetCity.lat,
                    targetCity.lon,
                    guessedCity.lat,
                    guessedCity.lon
                );
                const bearing = getBearing(
                    guessedCity.lat,
                    guessedCity.lon,
                    targetCity.lat,
                    targetCity.lon
                );
                const direction = getDirectionEmoji(bearing);

                const guessElement = document.createElement("div");
                guessElement.className = "guess";

                if (distance < 50) {
                    guessElement.classList.add("correct");
                } else if (distance < 500) {
                    guessElement.classList.add("close");
                } else {
                    guessElement.classList.add("far");
                }

                guessElement.innerHTML = `
                    <span>${guessedCity.name.toUpperCase()}</span>
                    <span class="distance">${distance.toFixed(2)} km</span>
                    <span class="direction">${direction}</span>
                `;
                guessesContainer.appendChild(guessElement);
                cityInput.value = "";
            } else {
                alert("City not found. Please try again.");
            }
        }
    });

    // Mock city-finding logic
    function findCity(cityName) {
        const cities = [
            { name: "Hyderabad", lat: 17.385, lon: 78.4867 },
            { name: "Shenzhen", lat: 22.5431, lon: 114.0579 },
            { name: "Tokyo", lat: 35.6895, lon: 139.6917 },
            { name: "Osaka", lat: 34.6937, lon: 135.5023 }
        ];
        return cities.find(
            (city) => city.name.toLowerCase() === cityName.toLowerCase()
        );
    }

    // Add distance and bearing functions here
    function calculateDistance(lat1, lon1, lat2, lon2) {
        // Use haversine formula here
        const R = 6371;
        const dLat = ((lat2 - lat1) * Math.PI) / 180;
        const dLon = ((lon2 - lon1) * Math.PI) / 180;
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos((lat1 * Math.PI) / 180) *
                Math.cos((lat2 * Math.PI) / 180) *
                Math.sin(dLon / 2) *
                Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    function getBearing(lat1, lon1, lat2, lon2) {
        const dLon = ((lon2 - lon1) * Math.PI) / 180;
        const lat1Rad = (lat1 * Math.PI) / 180;
        const lat2Rad = (lat2 * Math.PI) / 180;

        const y = Math.sin(dLon) * Math.cos(lat2Rad);
        const x =
            Math.cos(lat1Rad) * Math.sin(lat2Rad) -
            Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);

        let bearing = (Math.atan2(y, x) * 180) / Math.PI;
        return (bearing + 360) % 360;
    }

    function getDirectionEmoji(bearing) {
        if (bearing >= 22.5 && bearing < 67.5) return "↗️";
        if (bearing >= 67.5 && bearing < 112.5) return "➡️";
        if (bearing >= 112.5 && bearing < 157.5) return "↘️";
        if (bearing >= 157.5 && bearing < 202.5) return "⬇️";
        if (bearing >= 202.5 && bearing < 247.5) return "↙️";
        if (bearing >= 247.5 && bearing < 292.5) return "⬅️";
        if (bearing >= 292.5 && bearing < 337.5) return "↖️";
        return "⬆️";
    }
});
