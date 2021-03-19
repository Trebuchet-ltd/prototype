
var navbar = document.getElementById("itembar");
var sticky = navbar.offsetTop-58;
$(window).scroll(function () {


    if (window.pageYOffset >= sticky) {
        navbar.classList.add("sticky")
    } else {
        navbar.classList.remove("sticky");
    }

    if ($(window).scrollTop() > 10) {
        console.log('hello')
        $("#navbar").css("background-image", 'url("/static/images/NAV BAR.svg")');
    } else {
        $("#navbar").css("background-image", "");
    }
});
// If Mobile, add background color when toggler is clicked
$(".navbar-toggler").click(function () {
    if (!$(".navbar-collapse").hasClass("show")) {
        $("#navbar").css("background-image", 'url("/static/images/NAV BAR.svg")');
    } else {

        if ($(window).scrollTop() < 10) {
            $("#navbar").css("background-image", "");

        } else {
            $("#navbar").css("background-image", 'url("/static/images/NAV BAR.svg")');
        }
    }
});
// ############
let move = 1
// document ready
$(document).ready(() => {


    var myCarousel = document.getElementById('carouselExampleIndicators1')
    var PicCarousel = document.getElementById('carouselExampleIndicators')

    PicCarousel.addEventListener('slide.bs.carousel', function (e) {
        console.log(e.direction)
        if (move) {
            move = 0
            if (e.direction === 'left') {

                bootstrap.Carousel.getInstance(myCarousel).next()
            } else {
                bootstrap.Carousel.getInstance(myCarousel).prev()
            }
            move = 1
        }

    })
    myCarousel.addEventListener('slide.bs.carousel', function (e) {
        console.log(e.direction)
        if (move) {
            move = 0
            if (e.direction === 'left') {
                bootstrap.Carousel.getInstance(PicCarousel).next()
            } else {
                bootstrap.Carousel.getInstance(PicCarousel).prev()
            }
            move = 1
        }
    })

});
