$('.cart_quantity').change(function () {
    console.log(this.value);
    var ids = $(this).siblings('input').val()

    var csrf = $('input[name="csrfmiddlewaretoken"]').val();
    if (this.value > 0) {
        updateCartQuantity(ids, this.value, csrf)
    }
});

$('.deleteitemfromcart').click(function () {

    var ids = $(this).siblings('input').val()

    var csrf = $('input[name="csrfmiddlewaretoken"]').val();
    deleteCartQuantity(ids, csrf)

});

function updateCartQuantity(ids, val, csrftoken) {
    $.ajax({
            type: "POST",
            url: `/update/${ids}`,
            // data: formData,
            dataType: "json",
            data: {
                cart_quantity: val,
                csrfmiddlewaretoken: csrftoken
            },
            encode: true,
            success: function (data) {
                console.log(data)
                $('.toast').toast('hide')
                addToast('Success', `Successfully updated cart`)
                key = data['key']
                document.getElementById(key).innerText = "₹" + data[key]
                $(".total").text(data['total'])
            },
            error: function (data) {
                addToast('Failure', `Failed to update cart`)
            }
        }
    )
}

function deleteCartQuantity(ids, csrftoken) {

    $.ajax({
            type: "POST",
            url: `/delete/${ids}`,
            // data: formData,
            dataType: "json",
            data: {
                csrfmiddlewaretoken: csrftoken
            },
            encode: true,
            success: function (data) {
                console.log(data)
                $('.toast').toast('hide')
                $(`#${ids}_row`).remove()
                addToast('Success', `Successfully deleted item`)
                // key = data['key']
                // document.getElementById(key).innerText = "₹" + data[key]
               $(".total").text(data['total'])
                $(".items").text(data['items'])
            },
            error: function (data) {
                addToast('Failure', `Failed to update cart`)
            }
        }
    )
}

