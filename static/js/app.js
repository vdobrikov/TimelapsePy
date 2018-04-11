$(document).ready(function(){
    var image = $("#cam-preview-img");
    function updateImage() {
        image.attr("src", image.attr("src").split("?")[0]+"?" + Math.random());
    }
    // setInterval(updateImage, 5000);

    $('#cam-preview-controls-refresh').on('click', function (e) {
        updateImage();
    })

    var divTime = $("#current-time");
    function updateTime() {
        $.get('/api/now', function(data){
            divTime.text(data);
        }).fail(function(err) {
            console.error(err);
        });
    }
    setInterval(updateTime, 1000);

});