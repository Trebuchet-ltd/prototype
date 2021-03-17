$(window).scroll(function () {
    if ($(window).scrollTop() > 10  ) {
        console.log('hello')
        $(".navbar").css("background-image", 'url("/static/images/NAV BAR.svg")');
    } else {
        $(".navbar").css("background-image", "");
    }
});
// If Mobile, add background color when toggler is clicked
$(".navbar-toggler").click(function () {
    if (!$(".navbar-collapse").hasClass("show")) {
    } else {
       $(".navbar").css("background-image", 'url("/static/images/NAV BAR.svg")');
        if ($(window).scrollTop() < 10) {
            $(".navbar").css("background-image", "");
        } else {
        }
    }
});
// ############

// document ready
