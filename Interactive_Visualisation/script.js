let appData = {
    users_list: [],
    transitions_list: [],
    trajectories_list: [],
    obscured_observations: [],
    observations: [],
    obsCoordsMap: {}
};

async function fetchAndParseUsers() {
    try {
        const [usersRes, transRes, trajRes, obsRes, allObsRes] = await Promise.all([
            fetch('../Preprocessed_Dataset/users_list.json'),
            fetch('../Preprocessed_Dataset/transitions_list.json'),
            fetch('../Preprocessed_Dataset/trajectories_list.json'),
            fetch('../Preprocessed_Dataset/obscured_observations.json'),
            fetch('../Preprocessed_Dataset/observations.json')
        ]);

        appData.users_list = await usersRes.json();
        appData.transitions_list = await transRes.json();
        appData.trajectories_list = await trajRes.json();
        appData.obscured_observations = await obsRes.json();
        appData.observations = await allObsRes.json();

        for (let obs of appData.observations) {
            appData.obsCoordsMap[obs.observation_id] = { lat: obs.lat, lon: obs.long };
        }

        const users = appData.users_list.map(u => String(u.username));
        console.log(`Found ${users.length} users in JSON.`);
        return users;
    } catch (error) {
        console.error('Error fetching JSON data:', error);
        return [];
    }
}

// Store the currently selected user
let currentUser = null;
let selectedDate = [];
let leafletMap = null;
let currentMarkers = [];
let isDraggingTimeline = false;
let globalDaysArray = [];

document.addEventListener('mouseup', () => {
    if (isDraggingTimeline) {
        isDraggingTimeline = false;
        if (currentUser) {
            updateMapForDate(currentUser, selectedDate);
        }
    }
});

// Set the map, the timeline and load the pdf files
function setUser(user_id) {
    selectedDate = [];
    currentUser = user_id;
    console.log(`Great news ${user_id}`);
    setTimeline(user_id);
    renderPlotlyProfile(user_id);
}


let isColorblindMode = false;

const colorPaletteStandard = {
    c0: 'rgb(0, 0, 0)',
    c5: 'rgb(26, 150, 65)',
    c10: 'rgb(166, 217, 106)',
    c25: 'rgb(203, 203, 15)',
    c80: 'rgb(253, 174, 97)',
    c200: 'rgb(215, 25, 28)',
    cMax: 'rgb(129, 15, 124)'
};

const colorPaletteColorblind = {
    c0: 'rgb(0, 0, 0)',
    c5: 'rgb(27, 120, 55)',
    c10: 'rgb(127, 191, 123)',
    c25: 'rgb(217, 240, 211)',
    c80: 'rgb(231, 212, 232)',
    c200: 'rgb(175, 141, 195)',
    cMax: 'rgb(118, 42, 131)'
};

// Function to get color from speed
function getSpeedColor(speedStr) {
    if (!speedStr) return 'gray';
    const numMatch = speedStr.match(/[\d.]+/);
    if (!numMatch) return 'gray';
    const speed = parseFloat(numMatch[0]);

    const p = isColorblindMode ? colorPaletteColorblind : colorPaletteStandard;

    if (speed === 0) return p.c0;
    if (speed < 5) return p.c5;
    if (speed < 10) return p.c10;
    if (speed < 25) return p.c25;
    if (speed < 80) return p.c80;
    if (speed < 200) return p.c200;
    return p.cMax;
}

// Function for async sleep
const sleep = ms => new Promise(r => setTimeout(r, ms));



let plotlyShapesCache = {};
// Maps transition_id -> shape index, and observation_id -> shape index in the Plotly shapes array
let shapeIndexMap = {};

async function renderPlotlyProfile(user_id) {
    try {
        shapeIndexMap = {}; // Reset shape-to-index mapping for new user

        const userTransitions = appData.transitions_list.filter(t => String(t.user_id) === String(user_id));
        const userObscured = appData.obscured_observations.filter(o => String(o.user_id) === String(user_id));
        const userObservations = appData.observations.filter(o => String(o.user_id) === String(user_id));

        let transitionObsIds = new Set();
        for (let t of userTransitions) {
            transitionObsIds.add(String(t.observation_id1).replace('iN-p', '').replace('iN-o', ''));
            transitionObsIds.add(String(t.observation_id2).replace('iN-p', '').replace('iN-o', ''));
        }
        let isolatedObs = userObservations.filter(o => !transitionObsIds.has(String(o.observation_id)));

        let shapeList = [];
        let markerSize = 8.0;
        let dataEntryCounter = 0;
        let validDatesPlotly = new Set();

        // Group transitions by date
        let transitionsByDate = {};
        for (let t of userTransitions) {
            let d = t.date.trim();
            if (!transitionsByDate[d]) transitionsByDate[d] = [];
            transitionsByDate[d].push(t);
            validDatesPlotly.add(d.replace(/\//g, '-'));
        }

        // Group obscured by date
        let obscuredByDate = {};
        for (let o of userObscured) {
            let d = o.date.trim();
            if (!obscuredByDate[d]) obscuredByDate[d] = [];
            obscuredByDate[d].push(o);
            validDatesPlotly.add(d.replace(/\//g, '-'));
        }

        // Group isolated by date
        let isolatedByDate = {};
        for (let o of isolatedObs) {
            let d = o.date.trim().substring(0, 10).replace(/-/g, '/');
            if (!isolatedByDate[d]) isolatedByDate[d] = [];
            isolatedByDate[d].push(o);
            validDatesPlotly.add(d.replace(/\//g, '-'));
        }

        // Get all unique dates sorted
        let allDates = Array.from(new Set([...Object.keys(transitionsByDate), ...Object.keys(obscuredByDate), ...Object.keys(isolatedByDate)])).sort();

        for (let date of allDates) {
            dataEntryCounter += 1;
            let horizontalOffset = 0.0;

            let dateAnchor = date.replace(/\//g, '-');
            let trans = transitionsByDate[date] || [];
            let obs = obscuredByDate[date] || [];
            let isolated = isolatedByDate[date] || [];

            // Draw obscured shapes first (as squares)
            for (let o of obs) {
                let shapeIdx = shapeList.length;
                shapeIndexMap['obs_' + String(o.observation_id)] = shapeIdx;
                shapeList.push({
                    type: "rect",
                    xsizemode: 'pixel', ysizemode: 'pixel',
                    xanchor: dateAnchor,
                    yanchor: dataEntryCounter,
                    x0: markerSize * 0.5 + horizontalOffset, y0: -markerSize * 0.5,
                    x1: markerSize * 1.5 + horizontalOffset, y1: markerSize * 0.5,
                    line: { color: 'black', width: 1 },
                    fillcolor: 'white'
                });
                horizontalOffset += markerSize;
            }

            // Draw isolated shapes as green circles
            for (let o of isolated) {
                let shapeIdx = shapeList.length;
                shapeIndexMap['obs_' + String(o.observation_id)] = shapeIdx;
                shapeList.push({
                    type: "circle",
                    xsizemode: 'pixel', ysizemode: 'pixel',
                    xanchor: dateAnchor,
                    yanchor: dataEntryCounter,
                    x0: markerSize * 0.5 + horizontalOffset, y0: -markerSize * 0.5,
                    x1: markerSize * 1.5 + horizontalOffset, y1: markerSize * 0.5,
                    line: { width: 0 },
                    fillcolor: 'rgb(26, 150, 65)' // Green for isolated unobscured observations
                });
                horizontalOffset += markerSize;
            }

            // Draw first unobscured point if trans exists
            if (trans.length > 0) {
                let firstShapeIdx = shapeList.length;
                // Tag with the first observation_id of the first transition
                shapeIndexMap['obs_' + String(trans[0].observation_id1)] = firstShapeIdx;
                shapeList.push({
                    type: "circle",
                    xsizemode: 'pixel', ysizemode: 'pixel',
                    xanchor: dateAnchor,
                    yanchor: dataEntryCounter,
                    x0: markerSize * 0.5 + horizontalOffset, y0: -markerSize * 0.5,
                    x1: markerSize * 1.5 + horizontalOffset, y1: markerSize * 0.5,
                    line: { width: 0 },
                    fillcolor: 'rgb(128,128,128)' // First point is grey
                });
                horizontalOffset += markerSize;
            }

            // Draw remaining transitions
            for (let t of trans) {
                let additionalOffset = t.distance >= 0 ? Math.log2(t.distance + 1.0) : 0;
                horizontalOffset += additionalOffset;

                let fillcolorBySpeed = getSpeedColor(t.speed + " km/h");
                if (t.elapsed_time === 0) fillcolorBySpeed = 'rgb(0,0,0)'; // instantaneous

                let tShapeIdx = shapeList.length;
                // Tag with transition_id and also second observation_id
                shapeIndexMap['trans_' + String(t.transition_id)] = tShapeIdx;
                shapeIndexMap['obs_' + String(t.observation_id2)] = tShapeIdx;
                shapeList.push({
                    type: "circle",
                    xsizemode: 'pixel', ysizemode: 'pixel',
                    xanchor: dateAnchor,
                    yanchor: dataEntryCounter,
                    x0: markerSize * 0.5 + horizontalOffset, y0: -markerSize * 0.5,
                    x1: markerSize * 1.5 + horizontalOffset, y1: markerSize * 0.5,
                    line: { width: 0 },
                    fillcolor: fillcolorBySpeed
                });
                horizontalOffset += markerSize;
            }
        }

        plotlyShapesCache[user_id] = shapeList;

        const dummyX = shapeList.map(s => s.xanchor);
        const dummyY = shapeList.map(s => s.yanchor);
        const hoverInfo = dummyX.map(x => validDatesPlotly.has(x) ? 'all' : 'skip');

        const dummyData = [{
            x: dummyX,
            y: dummyY,
            mode: 'markers',
            marker: { opacity: 0 },
            hoverinfo: hoverInfo
        }];

        let layout = {
            margin: { l: 80, r: 10, b: 40, t: 10, pad: 4 },
            font: { size: 10 },
            showlegend: false,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: {
                tickangle: 0,
                tickformat: '%Y',
                gridwidth: 0.5,
                gridcolor: 'rgb(230,230,230)',
            },
            yaxis: {
                range: [0, dataEntryCounter + 1.5],
                zeroline: true,
                zerolinewidth: 1,
                zerolinecolor: '#2a3f5f',
                gridwidth: 0.5,
                gridcolor: 'rgb(230,230,230)',
            },
            shapes: shapeList
        };

        Plotly.newPlot('mppPlotly', dummyData, layout, { responsive: true });

        document.getElementById('mppPlotly').on('plotly_click', function (data) {
            if (data.points && data.points.length > 0) {
                const clickedDateString = data.points[0].x;
                if (!validDatesPlotly.has(clickedDateString)) return;

                const clickedDate = clickedDateString.replace(/-/g, '/');

                if (selectedDate.includes(clickedDate)) {
                    selectedDate = selectedDate.filter(d => d !== clickedDate);
                } else {
                    selectedDate.push(clickedDate);
                }
                console.log(`Plotly point clicked! Date: ${clickedDate}`);

                const allDays = document.querySelectorAll('.timeline-day');
                allDays.forEach(el => {
                    if (selectedDate.includes(el.textContent)) {
                        el.classList.add('selected');
                    } else {
                        el.classList.remove('selected');
                    }
                });

                updateMapForDate(user_id, selectedDate);
            }
        });

    } catch (error) {
        console.error('Error rendering Plotly Profile:', error);
    }
}

function highlightPlotlyDay(user_id, dates) {
    if (!plotlyShapesCache[user_id]) return;
    const shapes = plotlyShapesCache[user_id];
    const formattedDates = dates.map(d => d.replace(/\//g, '-'));

    // Create a new array of shapes to trigger relayout
    const updatedShapes = shapes.map(shape => {
        if (formattedDates.includes(shape.xanchor)) {
            return {
                ...shape,
                opacity: 1,
                line: shape.fillcolor === 'white' || shape.fillcolor === 'rgb(255,255,255)'
                    ? { ...shape.line, color: 'black', width: 2 }
                    : { color: 'rgb(50,50,50)', width: 2 }
            };
        } else {
            return { ...shape, opacity: 0.15 };
        }
    });

    try {
        Plotly.relayout('mppPlotly', { shapes: updatedShapes });
    } catch (e) {
        console.error("Error highlighting Plotly day:", e);
    }
}

// Highlight a single shape on the Plotly profile when hovering a map element
let _lastHighlightedShapeIdx = null;
function highlightProfileShape(shapeIdx) {
    if (!currentUser || !plotlyShapesCache[currentUser]) return;
    if (_lastHighlightedShapeIdx === shapeIdx) return; // avoid redundant relayouts
    _lastHighlightedShapeIdx = shapeIdx;

    const shapes = plotlyShapesCache[currentUser];
    const formattedDates = selectedDate.map(d => d.replace(/\//g, '-'));

    const updatedShapes = shapes.map((shape, idx) => {
        let s = { ...shape };
        // Keep day-based dimming
        if (formattedDates.length > 0) {
            s.opacity = formattedDates.includes(shape.xanchor) ? 1 : 0.15;
        }
        // Add highlight ring on the hovered shape
        if (idx === shapeIdx) {
            s.line = { color: 'rgba(255, 0, 0, 1)', width: 3 };
        }
        return s;
    });

    try {
        Plotly.relayout('mppPlotly', { shapes: updatedShapes });
    } catch (e) { /* ignore */ }
}

function clearProfileHighlight() {
    if (_lastHighlightedShapeIdx === null) return;
    _lastHighlightedShapeIdx = null;
    // Re-apply the normal day highlighting
    if (currentUser) {
        highlightPlotlyDay(currentUser, selectedDate);
    }
}

// Read log again to find observations for that user on that specific date
async function updateMapForDate(user_id, dates) {
    try {
        highlightPlotlyDay(user_id, dates);

        currentMarkers.forEach(marker => leafletMap.removeLayer(marker));
        currentMarkers = [];

        var circleIcon = L.icon({
            iconUrl: 'ressources/circle_icon.png',
            shadowUrl: 'ressources/circle_icon.png',
            iconSize: [20, 20],
            shadowSize: [0, 0],
            iconAnchor: [10, 10],
            shadowAnchor: [10, 10],
            popupAnchor: [0, -10]
        });

        const isAnimated = document.getElementById('animate-path') && document.getElementById('animate-path').checked;
        let bounds = L.latLngBounds();

        const userTransitions = appData.transitions_list.filter(t => String(t.user_id) === String(user_id) && dates.includes(t.date.trim()));
        const userObscured = appData.obscured_observations.filter(o => String(o.user_id) === String(user_id) && dates.includes(o.date.trim()));
        const userObservations = appData.observations.filter(o => String(o.user_id) === String(user_id) && dates.includes(o.date.trim().substring(0, 10).replace(/-/g, '/')));

        let transitionObsIds = new Set();
        for (let t of userTransitions) {
            transitionObsIds.add(String(t.observation_id1).replace('iN-p', '').replace('iN-o', ''));
            transitionObsIds.add(String(t.observation_id2).replace('iN-p', '').replace('iN-o', ''));
        }
        let isolatedObs = userObservations.filter(o => !transitionObsIds.has(String(o.observation_id)));

        if (userTransitions.length === 0 && userObscured.length === 0 && isolatedObs.length === 0) {
            console.log("No valid points to display for this date.");
            return;
        }

        // Draw unobscured points
        let addedPoints = new Set();
        for (let t of userTransitions) {
            let id1 = String(t.observation_id1).replace('iN-p', '').replace('iN-o', '');
            let id2 = String(t.observation_id2).replace('iN-p', '').replace('iN-o', '');
            let p1 = appData.obsCoordsMap[id1];
            let p2 = appData.obsCoordsMap[id2];

            if (p1 && !addedPoints.has(t.observation_id1)) {
                const marker = L.marker([p1.lat, p1.lon], { icon: circleIcon }).addTo(leafletMap);
                marker.bindTooltip(`<b>ID:</b> ${t.observation_id1}<br><b>Lat:</b> ${p1.lat.toFixed(5)}<br><b>Lon:</b> ${p1.lon.toFixed(5)}<br><b>Date:</b> ${t.date}`);
                // Highlight the corresponding profile shape on hover
                const obsKey1 = 'obs_' + String(t.observation_id1);
                marker.on('mouseover', () => { if (shapeIndexMap[obsKey1] !== undefined) highlightProfileShape(shapeIndexMap[obsKey1]); });
                marker.on('mouseout', clearProfileHighlight);
                currentMarkers.push(marker);
                bounds.extend([p1.lat, p1.lon]);
                addedPoints.add(t.observation_id1);
            }
            if (p2 && !addedPoints.has(t.observation_id2)) {
                const marker = L.marker([p2.lat, p2.lon], { icon: circleIcon }).addTo(leafletMap);
                marker.bindTooltip(`<b>ID:</b> ${t.observation_id2}<br><b>Lat:</b> ${p2.lat.toFixed(5)}<br><b>Lon:</b> ${p2.lon.toFixed(5)}<br><b>Date:</b> ${t.date}`);
                const obsKey2 = 'obs_' + String(t.observation_id2);
                marker.on('mouseover', () => { if (shapeIndexMap[obsKey2] !== undefined) highlightProfileShape(shapeIndexMap[obsKey2]); });
                marker.on('mouseout', clearProfileHighlight);
                currentMarkers.push(marker);
                bounds.extend([p2.lat, p2.lon]);
                addedPoints.add(t.observation_id2);
            }
        }

        // Draw isolated unobscured points
        for (let o of isolatedObs) {
            let p1 = { lat: o.lat, lon: o.long };
            if (!addedPoints.has(String(o.observation_id))) {
                const marker = L.marker([p1.lat, p1.lon], { icon: circleIcon }).addTo(leafletMap);
                marker.bindTooltip(`<b>ID:</b> ${o.observation_id}<br><b>Lat:</b> ${p1.lat.toFixed(5)}<br><b>Lon:</b> ${p1.lon.toFixed(5)}<br><b>Date:</b> ${o.date}`);
                const obsKey = 'obs_' + String(o.observation_id);
                marker.on('mouseover', () => { if (shapeIndexMap[obsKey] !== undefined) highlightProfileShape(shapeIndexMap[obsKey]); });
                marker.on('mouseout', clearProfileHighlight);
                currentMarkers.push(marker);
                bounds.extend([p1.lat, p1.lon]);
                addedPoints.add(String(o.observation_id));
            }
        }

        console.log(`Currently displaying ${addedPoints.size} observations on the map.`);

        // Obscured points are intentionally NOT drawn on the map because they lack precise coordinates.

        leafletMap.fitBounds(bounds, { padding: [50, 50] });
        if (isAnimated) await sleep(800);

        for (let t of userTransitions) {
            let id1 = String(t.observation_id1).replace('iN-p', '').replace('iN-o', '');
            let id2 = String(t.observation_id2).replace('iN-p', '').replace('iN-o', '');
            let p1 = appData.obsCoordsMap[id1];
            let p2 = appData.obsCoordsMap[id2];
            if (!p1 || !p2) continue;

            let color = getSpeedColor(t.speed + " km/h");

            const polyline = L.polyline([[p1.lat, p1.lon], [p2.lat, p2.lon]], {
                color: color,
                weight: 4,
                opacity: 0.8
            }).addTo(leafletMap);

            let transInfo = `<b>Speed:</b> ${parseFloat(t.speed).toFixed(2)} km/h<br><b>Distance:</b> ${parseFloat(t.distance).toFixed(2)} m<br><b>Elapsed Time:</b> ${parseFloat(t.elapsed_time).toFixed(0)} s`;
            if (t.acceleration !== undefined) {
                transInfo += `<br><b>Acceleration:</b> ${parseFloat(t.acceleration).toFixed(4)} m/s²`;
            }
            if (t.bearing_change !== undefined) {
                transInfo += `<br><b>Bearing Change:</b> ${parseFloat(t.bearing_change).toFixed(2)}°`;
            }
            // sticky: true makes the tooltip follow the mouse along the polyline
            polyline.bindTooltip(transInfo, { sticky: true });

            // Highlight the corresponding profile shape on hover
            const transKey = 'trans_' + String(t.transition_id);
            polyline.on('mouseover', () => { if (shapeIndexMap[transKey] !== undefined) highlightProfileShape(shapeIndexMap[transKey]); });
            polyline.on('mouseout', clearProfileHighlight);
            currentMarkers.push(polyline);

            const p1_proj = leafletMap.project([p1.lat, p1.lon]);
            const p2_proj = leafletMap.project([p2.lat, p2.lon]);
            const angle = Math.atan2(p2_proj.y - p1_proj.y, p2_proj.x - p1_proj.x) * 180 / Math.PI;
            const midLat = (p1.lat + p2.lat) / 2;
            const midLon = (p1.lon + p2.lon) / 2;

            const arrowIcon = L.divIcon({
                className: 'custom-arrow-icon',
                html: `
                    <div style="width: 20px; height: 20px; transform: rotate(${angle}deg);">
                        <svg viewBox="0 0 24 24" width="20" height="20" style="overflow: visible;">
                            <polygon points="4,4 20,12 4,20" fill="${color}" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                `,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            const arrowMarker = L.marker([midLat, midLon], { icon: arrowIcon, interactive: true }).addTo(leafletMap);
            arrowMarker.bindTooltip(transInfo, { sticky: true });
            arrowMarker.on('mouseover', () => { if (shapeIndexMap[transKey] !== undefined) highlightProfileShape(shapeIndexMap[transKey]); });
            arrowMarker.on('mouseout', clearProfileHighlight);
            currentMarkers.push(arrowMarker);

            if (isAnimated) await sleep(400);
        }

    } catch (error) {
        console.error('Error updating map:', error);
    }
}

async function setTimeline(user_id) {
    try {
        const activeDays = new Set();

        // Find all days with unobscured transitions for this user
        appData.transitions_list.forEach(t => {
            if (String(t.user_id) === String(user_id) && t.date.includes('/')) {
                activeDays.add(t.date.trim());
            }
        });

        // Add days with obscured observations
        appData.obscured_observations.forEach(o => {
            if (String(o.user_id) === String(user_id)) {
                let d = o.date.trim().substring(0, 10).replace(/-/g, '/');
                activeDays.add(d);
            }
        });

        // Add days with isolated observations
        appData.observations.forEach(o => {
            if (String(o.user_id) === String(user_id)) {
                let d = o.date.trim().substring(0, 10).replace(/-/g, '/');
                activeDays.add(d);
            }
        });

        globalDaysArray = Array.from(activeDays).sort();
        console.log(`User ${user_id} has observations on ${globalDaysArray.length} unique days.`);

        renderTimeline();

        return globalDaysArray;

    } catch (error) {
        console.error('Error generating timeline:', error);
        return [];
    }
}

// --- Timeline Framework ---

function buildTimelineTokens(mode, daysArray) {
    if (!daysArray || daysArray.length === 0) return [];

    if (mode === 'day') {
        return daysArray.map(day => ({ label: day, days: [day] }));
    }
    else if (mode === 'month') {
        const monthsMap = {};
        daysArray.forEach(day => {
            const parts = day.split('/');
            if (parts.length >= 2) {
                const monthLabel = parts[0] + '/' + parts[1];
                if (!monthsMap[monthLabel]) monthsMap[monthLabel] = [];
                monthsMap[monthLabel].push(day);
            }
        });
        return Object.keys(monthsMap).sort().map(month => ({ label: month, days: monthsMap[month] }));
    }
    else if (mode === 'year') {
        const yearsMap = {};
        daysArray.forEach(day => {
            const parts = day.split('/');
            if (parts.length >= 1) {
                const yearLabel = parts[0];
                if (!yearsMap[yearLabel]) yearsMap[yearLabel] = [];
                yearsMap[yearLabel].push(day);
            }
        });
        return Object.keys(yearsMap).sort().map(year => ({ label: year, days: yearsMap[year] }));
    }
    else if (mode === 'smart') {
        // This mode clusters observations that were done in maximum 5 days in a row, and returns the 5 most important clusters
        let clusters = [];
        let currentCluster = { label: '', days: [] };
        let prevDate = null;

        daysArray.forEach(day => {
            const currDate = new Date(day.replace(/\//g, '-'));
            if (!prevDate) {
                currentCluster.days.push(day);
            } else {
                const diffTime = Math.abs(currDate - prevDate);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                if (diffDays > 5) {
                    clusters.push(currentCluster);
                    currentCluster = { label: '', days: [day] };
                } else {
                    currentCluster.days.push(day);
                }
            }
            prevDate = currDate;
        });
        if (currentCluster.days.length > 0) {
            clusters.push(currentCluster);
        }

        clusters.sort((a, b) => b.days.length - a.days.length);
        const topClusters = clusters.slice(0, 5);
        topClusters.sort((a, b) => a.days[0].localeCompare(b.days[0]));

        return topClusters.map(cluster => {
            const startNode = cluster.days[0];
            const endNode = cluster.days[cluster.days.length - 1];
            return {
                label: startNode === endNode ? startNode : `${startNode} to ${endNode}`,
                days: cluster.days
            };
        });
    }
    return [];
}

function renderTimeline() {
    const timelineList = document.getElementById('timeline');
    const modeSelect = document.getElementById('timeline-mode');
    if (!timelineList || !modeSelect) return;

    timelineList.innerHTML = '';
    const mode = modeSelect.value;
    const tokens = buildTimelineTokens(mode, globalDaysArray);

    tokens.forEach(token => {
        const li = document.createElement('li');
        li.className = 'timeline-day';
        li.textContent = token.label;

        const isFullySelected = token.days.length > 0 && token.days.every(d => selectedDate.includes(d));
        if (isFullySelected) {
            li.classList.add('selected');
        }

        li.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isDraggingTimeline = true;

            const currentlySelected = token.days.every(d => selectedDate.includes(d));
            if (currentlySelected) {
                selectedDate = selectedDate.filter(d => !token.days.includes(d));
                li.classList.remove('selected');
            } else {
                token.days.forEach(d => {
                    if (!selectedDate.includes(d)) selectedDate.push(d);
                });
                li.classList.add('selected');
            }
        });

        li.addEventListener('mouseenter', () => {
            if (isDraggingTimeline) {
                const currentlySelected = token.days.every(d => selectedDate.includes(d));
                if (currentlySelected) {
                    selectedDate = selectedDate.filter(d => !token.days.includes(d));
                    li.classList.remove('selected');
                } else {
                    token.days.forEach(d => {
                        if (!selectedDate.includes(d)) selectedDate.push(d);
                    });
                    li.classList.add('selected');
                }
            }
        });

        timelineList.appendChild(li);
    });
}

async function loadObservationsList() {
    try {
        const response = await fetch('../observations_list.txt');
        if (!response.ok) throw new Error('observations_list.txt not found');
        const text = await response.text();
        const files = text.split('\n').filter(line => line.trim() !== '');
        console.log(`Loaded ${files.length} observation files:`, files);
        return files;
    } catch (error) {
        console.error('Error loading observations list:', error);
        return [];
    }
}

// Automatically load and populate the user-select dropdown when the page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Load available observation datasets into JS scope
    const availableCsvFiles = await loadObservationsList();
    console.log(`Les fichiers ${availableCsvFiles}`, availableCsvFiles);

    // 0. Initialize the Map
    leafletMap = L.map('map').setView([0, 0], 2); // Default to a global view

    // Log zoom level and hide arrows when zoomed out to improve performance
    function checkZoomLevel() {
        const currentZoom = leafletMap.getZoom();
        console.log(`Current map zoom level: ${currentZoom}`);
        if (currentZoom < 6) {
            leafletMap.getContainer().classList.add('hide-arrows');
        } else {
            leafletMap.getContainer().classList.remove('hide-arrows');
        }
    }
    leafletMap.on('zoomend', checkZoomLevel);
    checkZoomLevel(); // Initial check

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(leafletMap);

    // 0.5 Build Legend dynamically
    let legendControl = null;
    function updateLegend() {
        if (legendControl) leafletMap.removeControl(legendControl);

        legendControl = L.control({ position: 'bottomright' });
        legendControl.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'info legend');
            const p = isColorblindMode ? colorPaletteColorblind : colorPaletteStandard;
            const categories = [
                { threshold: '0 km/h', color: p.c0 },
                { threshold: '< 5 km/h', color: p.c5 },
                { threshold: '< 10 km/h', color: p.c10 },
                { threshold: '< 25 km/h', color: p.c25 },
                { threshold: '< 80 km/h', color: p.c80 },
                { threshold: '< 200 km/h', color: p.c200 },
                { threshold: '>= 200 km/h', color: p.cMax }
            ];
            div.innerHTML = '<strong>Speed Key</strong><br>';
            for (let i = 0; i < categories.length; i++) {
                div.innerHTML +=
                    '<i style="background-color:' + categories[i].color + '; display: inline-block; width: 50px; height: 16px; float: left; margin-right: 8px; margin-top: 3px; border-radius: 3px; border: 1px solid rgba(0, 0, 0, 0.2);"></i> ' +
                    categories[i].threshold + '<br>';
            }
            return div;
        };
        legendControl.addTo(leafletMap);
    }

    updateLegend();

    // Colorblind mode toggle listener
    const colorblindToggle = document.getElementById('colorblind-toggle');
    if (colorblindToggle) {
        colorblindToggle.addEventListener('change', (e) => {
            isColorblindMode = e.target.checked;
            updateLegend();

            // Clear Plotly cache to force recalculation of shape colors
            plotlyShapesCache = {};

            // Re-render visuals if a user is already active
            if (currentUser) {
                renderPlotlyProfile(currentUser);
                if (selectedDate) {
                    updateMapForDate(currentUser, selectedDate);
                }
            }
        });
    }

    // Timeline resolution toggle listener
    const timelineModeSelect = document.getElementById('timeline-mode');
    if (timelineModeSelect) {
        timelineModeSelect.addEventListener('change', () => {
            renderTimeline();
        });
    }

    // 1. Fetch the user list and stats
    const users = await fetchAndParseUsers();

    let usernames = {};
    try {
        const statsResponse = await fetch('ressources/usernames.json');
        if (statsResponse.ok) {
            usernames = await statsResponse.json();
        }
    } catch (e) { console.warn("Could not load usernames"); }

    // 2. Identify the select element
    const selectElement = document.getElementById('user-select');
    if (!selectElement) {
        console.warn('Could not find the element with ID "user-select"');
        return;
    }

    // Add a 'change' event listener to the <select> element itself
    selectElement.addEventListener('change', (event) => {
        // event.target.value contains the value of the selected option
        const selectedUserId = event.target.value;
        if (selectedUserId) {
            setUser(selectedUserId); // Pass the selected user to your function
        }
    });

    // Create a dictionary of user counts for fast lookup
    let userCounts = {};
    if (appData && appData.users_list) {
        for (const u of appData.users_list) {
            userCounts[String(u.username)] = u.nb_observations || 0;
        }
    }

    // Sort users by count descending
    users.sort((a, b) => {
        const countA = userCounts[a] || 0;
        const countB = userCounts[b] || 0;
        return countB - countA;
    });

    // Take top 1000 users to prevent native dropdown lag
    const topUsers = users.slice(0, 20000);

    // Create a document fragment to append options rapidly
    const fragment = document.createDocumentFragment();

    // Append each user as a new <option>
    for (const user of topUsers) {
        const option = document.createElement('option');
        option.value = user;
        const uname = usernames[user] || "Unknown";
        const count = userCounts[user] || 0;
        option.textContent = `${uname} (${count} obs)`;
        fragment.appendChild(option);
    }
    selectElement.appendChild(fragment);
});

function toggleProfile() {
    const chart = document.getElementById('chart-container');
    const btn = document.getElementById('toggle-profile');
    if (chart.classList.contains('hidden')) {
        chart.classList.remove('hidden');
        chart.style.width = ''; // Clear inline width so it snaps back to CSS default or previously expanded width
        btn.textContent = '▶';
        setTimeout(() => {
            if (window.Plotly) Plotly.Plots.resize('mppPlotly');
            if (leafletMap) leafletMap.invalidateSize();
        }, 300);
    } else {
        chart.classList.add('hidden');
        btn.textContent = '◀';
        setTimeout(() => {
            if (leafletMap) leafletMap.invalidateSize();
        }, 300);
    }
}

// Resizer logic
document.addEventListener('DOMContentLoaded', () => {
    const resizer = document.getElementById('resizer');
    const chart = document.getElementById('chart-container');
    const container = document.getElementById('content-split');

    if (!resizer || !chart || !container) return;

    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        chart.style.transition = 'none'; // Prevent CSS transition lagging during manual resize
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const containerRect = container.getBoundingClientRect();
        let newWidth = containerRect.right - e.clientX;

        if (newWidth < 50) {
            newWidth = 0;
            if (!chart.classList.contains('hidden')) {
                chart.classList.add('hidden');
                document.getElementById('toggle-profile').textContent = '◀';
            }
        } else {
            if (chart.classList.contains('hidden')) {
                chart.classList.remove('hidden');
                chart.style.width = ''; // Clear inline width to let it recover visually
                document.getElementById('toggle-profile').textContent = '▶';
            }
            if (newWidth > containerRect.width - 200) newWidth = containerRect.width - 200;
        }

        chart.style.width = newWidth + 'px';
        chart.style.flex = 'none'; // Ensure CSS flex-basis doesn't fight our inline width

        if (window.Plotly) Plotly.Plots.resize('mppPlotly');
        if (leafletMap) leafletMap.invalidateSize();
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            chart.style.transition = ''; // Restore transition
            if (leafletMap) leafletMap.invalidateSize();
        }
    });
});
