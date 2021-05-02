function addProductToCart(ids, el, title) {
    var elem = $(el).siblings('div')
    var val = $(elem).find('input[name="quantity"]').val()
    var csrf = $('input[name="csrfmiddlewaretoken"]').val()
    //console.log(val)

    addProductToCartPost(ids, val, csrf, title)
}

function addProductToCartPost(ids, val, csrftoken, title) {
    $.ajax({
            type: "POST",
            url: `/product/${ids}`,
            // data: formData,
            dataType: "json",
            data: {
                quantity: val,
                csrfmiddlewaretoken: csrftoken
            },
            encode: true,
            success: function (data) {
                //console.log(data)
                addToast('Success', `Successfully added ${val} ${title} to cart`)
            },
            error: function (data) {
                addToast('Failure', `Failed to add  ${title} to cart`)
            }
        }
    )
}

function filterCards(filter_keyword, element) {
    card_prod = $('.card_prod')
    $('.fa-times-circle').hide()

    if ($(element).hasClass('active')) {
        $('.nav-link').removeClass('active')
        card_prod.css({'display': 'block'})
        return
    }
    $(element).children().show()
    //console.log($(element).children())
    card_prod.css({'display': 'none'})
    $(`.${filter_keyword}`).css({'display': 'block'})
    $(element).addClass('active')
    //console.log($(element))

}

$('.fa-times-circle').hide()