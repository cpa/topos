function uuidv4() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

if (!localStorage.playerId) {
    const pId = uuidv4();
    console.log('Generating playerId:', pId);
    localStorage.playerId = pId;
} else {
    console.log('playerId found:', localStorage.playerId);
}

var svg, width, height;

function init() {
    width = window.innerWidth;
    height = window.innerHeight;
    svg = d3.select("body").selectAll("#chartArea").append('canvas').attr('width', width).attr('height', height);
}

init();

const playerId = localStorage.playerId;
const gameId = window.location.pathname.replace(/^\//, ''); // '/<uuid>' => '<uuid>'

var particles;
var particlesColors = Array();
var colors;
var currentColor;

var socket = io("{{ server_name }}");

socket.on('debug', (data) => {
    console.log('debug', data);
});

socket.on('connect', () => {
    socket.emit('hello', {playerId: playerId, gameId: gameId});
});

socket.on('refresh', (data) => {
    currentColor = data['currentColor'];
    particles = data['particles'];
    particles = particles.map((point) => [point[0] * width, point[1] * height, point[2]]);
    
    for (let i = 0, n = particles.length; i < n; i++) {
        particlesColors[i] = particles[i][2];
    }

    update();
});

svg.on("mousemove", function () {
    update([event.layerX, event.layerY]);
    socket.emit('mousemove', {playerId: playerId, gameId: gameId, data: [event.layerX/width, event.layerY/height, currentColor]});    
});

svg.on("mouseout", () => {
    update();
});

svg.on("click", function () {
    particles.push([event.layerX, event.layerY, currentColor]);
    particlesColors.push(currentColor);
    socket.emit('click', {playerId: playerId, gameId: gameId, data: [event.layerX/width, event.layerY/height, currentColor]});
    update();
});

////////////////////////////////////////////////////////////////////////////////////

const context = svg.node().getContext("2d");

function update(point) {
    var tmp = [...particles]; // C'est pour copier le tableau
    var tmpColors = [...particlesColors];

    if (point) {
        tmp.push(point);
        tmpColors.push(currentColor);
    }

    const delaunay = d3.Delaunay.from(tmp);
    const voronoi = delaunay.voronoi([0.5, 0.5, width - 0.5, height - 0.5]);
    context.clearRect(0, 0, width, height);

    for (let i = 0, n = tmp.length; i < n; ++i) {
        context.beginPath();
        voronoi.renderCell(i, context);
        context.fillStyle = tmpColors[i];
        context.strokeStyle = tmpColors[i];
        context.stroke();
        context.fill();
    }
    
    voronoi.render(context);
    voronoi.renderBounds(context);

    // context.beginPath();
    // delaunay.renderPoints(context);
}

// window.addEventListener("resize", () => { init(); update() });
