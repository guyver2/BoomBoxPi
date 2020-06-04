function updateStatus(data) { // TODO use this instead of reloading
    console.log(data)
    console.log(typeof data)
    let playlist = data.playlist.name.replace(/_/g, " ");
    if (data.track) {
        let title = data.track.title.replace(/_/g, " ");
        document.getElementById("nowPlaying").innerHTML = playlist + " - " + title;
    } else {
        document.getElementById("nowPlaying").innerHTML = playlist;
    }
    $("#lock").prop("checked", data.lock);
    $("#mute").prop("checked", data.mute);
}


function nextSong() {
    $.getJSON("api", { q: "nextSong" }, function (data) { updateStatus(data); });
}

function prevSong() {
    $.getJSON("api", { q: "previousSong" }, function (data) { updateStatus(data); });
}

function playPause() {
    $.getJSON("api", { q: "playPause" }, function (data) { updateStatus(data); });
}

function nextPlaylist() {
    $.getJSON("api", { q: "nextPlayList" }, function (data) { updateStatus(data); });
}

function requestPlaylist() {
    var select = document.getElementById("listPlaylist");
    var playlistID = select.options[select.selectedIndex].value;
    $.getJSON("api", { q: "request", value: "p " + playlistID }, function (data) { updateStatus(data); });
}

function requestTrack() {
    var select = document.getElementById("listTrack");
    var trackID = select.options[select.selectedIndex].value;
    $.getJSON("api", { q: "request", value: "t " + trackID }, function (data) { updateStatus(data); });
}

function lockUnlock() {
    var locked = $("#lock").is(':checked');
    if (locked) {
        $.get("api", { q: "lock" }, function (data) { updateStatus(data); });
    } else {
        $.get("api", { q: "unlock" }, function (data) { updateStatus(data); });
    }
}

function muteUnmute() {
    var muted = $("#mute").is(':checked');
    console.log(muted)
    if (muted) {
        $.getJSON("api", { q: "mute" }, function (data) { updateStatus(data); });
    } else {
        $.getJSON("api", { q: "unmute" }, function (data) { updateStatus(data); });
    }
}

function setVolume(volume) {
    console.log(volume)
    $.getJSON("api", { q: "volume", value: volume });
}

function requestContent(type, value) {
    $.getJSON("api", { q: "request", value: type + "  " + value }, function (data) { updateStatus(data); });
}