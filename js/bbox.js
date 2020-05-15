function updateStatus(data) {
    console.log(data)
    console.log(typeof data)
    let title = data.track.title.replace(/_/g, " ");
    let playlist = data.playlist.name.replace(/_/g, " ");
    document.getElementById("nowPlaying").innerHTML = playlist + " - " + title;
}


function nextSong() {
    $.getJSON("api", { q: "nextSong" }, function (data) { location.reload();/*updateStatus(data);*/ });
}

function prevSong() {
    $.getJSON("api", { q: "previousSong" }, function (data) { location.reload();/*updateStatus(data);*/ });
}

function playPause() {
    $.getJSON("api", { q: "playPause" }, function (data) { updateStatus(data); });
}

function nextPlaylist() {
    $.getJSON("api", { q: "nextPlayList" }, function (data) { location.reload();/*updateStatus(data);*/ });
}

function requestPlaylist() {
    var select = document.getElementById("listPlaylist");
    var playlistID = select.options[select.selectedIndex].value;
    $.getJSON("api", { q: "request", value: "p " + playlistID }, function (data) { location.reload();/*updateStatus(data);*/ });
}

function requestTrack() {
    var select = document.getElementById("listTrack");
    var trackID = select.options[select.selectedIndex].value;
    $.getJSON("api", { q: "request", value: "t " + trackID }, function (data) { location.reload(); /*updateStatus(data);*/ });
}

function lockUnlock() {
    var locked = $("#lock").is(':checked');
    if (locked) {
        $.get("api", { q: "lock" });
    } else {
        $.get("api", { q: "unlock" });
    }
}

function muteUnmute() {
    var muted = $("#mute").is(':checked');
    if (muted) {
        $.getJSON("api", { q: "mute" }, function (data) { updateStatus(data); });
    } else {
        $.getJSON("api", { q: "unmute" }, function (data) { updateStatus(data); });
    }
}

function requestContent(type, value) {
    $.getJSON("api", { q: "request", value: type + "  " + value }, function (data) { });
}