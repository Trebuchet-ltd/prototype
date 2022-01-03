const INITIAL_ROWS = 7;

let currentData = {};
let rowCount = 0;

function addRow() {
    let row = document.getElementById("invoice_row").content.cloneNode(true);

    const cRow = rowCount++ + INITIAL_ROWS;

    row.querySelector("#code").addEventListener("keyup", (e) => search(cRow, null, e.target.value));
    row.querySelector("#name").addEventListener("keyup", (e) => search(cRow, e.target.value));
    row.querySelector("#weight").addEventListener("keyup", () => calculateRow(cRow));
    row.querySelector("#quantity").addEventListener("keyup", () => calculateRow(cRow));

    document.getElementById("invoice-form-items-table-body").appendChild(row);
}

function calculateRow(rowId) {
    const row = document.getElementsByTagName("tr")[rowId];
    console.log(row, rowId);
    const price = Number(row.querySelector("#rate_wo_gst").value || 0) * 0.001 *
        Number(row.querySelector("#weight").value || 0) * Number(row.querySelector("#quantity").value || 0)

    if (!price)
        return;

    row.querySelector("#amt_wo_gst").value = price;
    row.querySelector("#amt").value = price +
        price * (Number(row.querySelector("#s_gst").value || 0) + Number(row.querySelector("#c_gst").value || 0));
}

async function fillRow(rowId, item) {
    const row = document.getElementsByTagName("tr")[rowId];

    row.querySelector("#id").value = item.id;
    row.querySelector("#code").value = item.code;
    row.querySelector("#name").value = item.title;
    row.querySelector("#weight").value = row.querySelector("#weight").value || 1;
    row.querySelector("#quantity").value = row.querySelector("#weight").value || 1;
    row.querySelector("#s_gst").value = item.product_gst_percentage / 2;
    row.querySelector("#c_gst").value = item.product_gst_percentage / 2;
    row.querySelector("#rate_wo_gst").value = item.price;

    calculateRow(rowId);
}

async function search(row, name, code = null) {
    if (currentData[code || name])
        return fillRow(row, currentData[code || name]);

    const results = await fetch(`/api/products/?${code ? "code" : "search"}=${name || code}`)
        .then((res) => res.json())
        .then((json) => json.results);

    results.forEach((result) => currentData[result.title] = currentData[result.code] = result);

    const options = results.map((result) => `<option data-id="${result.id}" value="${code ? result.code : result.title}" >`);

    document.getElementById("name_options").innerHTML = options.join("");
}

async function checkout() {
    const trs = document.querySelectorAll("tr");
    const products = [];

    for (let i = INITIAL_ROWS; i < rowCount + INITIAL_ROWS; i++) {
        const row = trs[i];

        const id = Number(row.querySelector("#id").value);
        const quantity = Number(row.querySelector("#quantity").value);
        const weight = Number(row.querySelector("#weight").value);
        const cleaned = Number(row.querySelector("#cleaned").checked);

        if (id && quantity && weight)
            products.push({id, quantity, weight, cleaned});
    }

    if (products.length) {
        const order = await fetch("/api/order/order/",
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.getElementsByName("csrfmiddlewaretoken")[0].value
                },
                credentials: "same-origin",
                method: "POST",
                body: JSON.stringify(
                    {
                        name: document.getElementById("customer-name-input").value,
                        address: document.getElementById("customer-address-input").value,
                        pincode: document.getElementById("customer-pin-input").value,
                        phone: document.getElementById("customer-phone-input").value,
                        products
                    }
                )
            });

        printBill(await order.json());
    } else
        window.alert("Fill the form !!!")
}

function printBill({total, order_item}) {
    const printWindow = window.open("", "Print Bill");
    let print = document.getElementById("print_content").innerHTML;

    console.log(order_item[0])

    const rows = order_item.map(({quantity, item}) =>
        `<tr>
            <td>${item.title}</td>
            <td>${item.weight}</td>
            <td>${quantity}</td>
            <td>${item.cleaned_price || item.product_rate_with_gst}</td>
        </tr>`
    );

    print = print.split("<tbody>").join(rows.join(""));
    print = print.split("<span>").join(total);
    print = print.split("<b>").join(total);

    printWindow.document.write('<html lang="en"><body style="font-family: sans-serif;">');
    printWindow.document.write(print);
    printWindow.document.write('</body></html>');
    printWindow.document.close();

    printWindow.focus();
    printWindow.print();
}

for (let i = 0; i < 5; i++)
    addRow();


document.getElementById("invoice-form").addEventListener("submit", (e) => {
    e.preventDefault();
    checkout().then();
});
