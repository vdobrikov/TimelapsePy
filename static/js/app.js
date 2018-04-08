$(document).ready(function(){
    var image = $("#img-cam-preview");
    function updateImage() {
        image.attr("src", image.attr("src").split("?")[0]+"?" + Math.random());
    }
    setInterval(updateImage, 1000);

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