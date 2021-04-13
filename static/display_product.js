function addProductToCart(ids, el, title) {
    var elem = $(el).siblings('div')
    var val = $(elem).find('input[name="quantity"]').val()
    var csrf = $('input[name="csrfmiddlewaretoken"]').val()
    console.log(val)

    addProductToCartPost(ids,val,csrf,title)
}

function addProductToCartPost(ids,val, csrftoken,title) {
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
                console.log(data)
                addToast('Success', `Successfully added ${val} ${title} to cart`)
            },
            error: function (data) {
                addToast('Failure', `Failed to add  ${title} to cart`)
            }
        }
    )
}