var navbar = document.getElementById("itembar");
var sticky = navbar.offsetTop - 58;
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
csrf = $('input[name="csrfmiddlewaretoken"]').val()

$.ajax({
    type: "GET",
    url: "/display",
    // data: formData,
    dataType: "json",
    encode: true,

    success: function (data) {
        let row_variable = document.createElement("div");
        row_variable.setAttribute("class", "row");

        let content = document.getElementById("content");
        content.appendChild(row_variable);
        console.log(content);
        for (let i = 0; i < data.length; i++) {
            console.log(data[i]);
            let display_products_var = `
            <div class="col col-6 col-xl-3 col-sm-6">    
                    <div class="el-wrapper">
                        <a href="/product/${data[i].id}">
                            <div class="box-up">
                            <img class="img" src="${data[i].images[0].mainimage}" alt="">
                            <div class="img-info">
                                <div class="info-inner">
                                    <span class="p-name">${data[i].title}</span>
                                    <span class="p-company">${data[i].description}</span>
                                </div>
                            </div>
                        </div>
                        </a>
                        <div class="box-down">
                            <div class="h-bg">
                                <div class="h-bg-inner"></div>
                            </div>
            
                            <a class="cart" onclick="addProductToCartPost(${data[i].id},1,'${csrf}','${data[i].title}')">
                                <span class="price">Rs ${data[i].price}</span>
                                <span class="add-to-cart">
                                    <span class="txt mobile-no-display">Add in cart</span>
                                </span>
                            </a>
                        </div>
            
                    </div>
               
            
            </div>
            `
            console.log(display_products_var)
            row_variable.innerHTML += display_products_var;


        }


    }
})




