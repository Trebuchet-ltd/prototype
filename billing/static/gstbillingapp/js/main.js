const INITIAL_ROWS = 7;

let currentData = {};
let rowCount = 0;

function addRow() {
    let row = document.getElementById("invoice_row").content.cloneNode(true);

    const cRow = rowCount++ + INITIAL_ROWS;

    row.querySelector("#sl_no").innerText = rowCount;
    row.querySelector("#code").addEventListener("keyup", (e) => search(cRow, null, e.target.value));
    row.querySelector("#name").addEventListener("keyup", (e) => search(cRow, e.target.value));
    row.querySelector("#weight").addEventListener("keyup", () => calculateRow(cRow));

    document.getElementById("invoice-form-items-table-body").appendChild(row);
    document.getElementsByTagName("tr")[cRow]
        .addEventListener("keyup", rowEventHandler);
}

function calculateTotal() {
    const trs = document.querySelectorAll("tr");
    let total = 0;

    for (let i = INITIAL_ROWS; i < rowCount + INITIAL_ROWS; i++)
        total += Number(trs[i].querySelector("#amt").value || 0);

    document.getElementById("invoice-total").value = total;
}

function calculateRow(rowId) {
    const row = document.getElementsByTagName("tr")[rowId];
    const price = Number(row.querySelector("#rate_wo_gst").value || 0) *
        Number(row.querySelector("#weight").value || 0)

    row.querySelector("#amt_wo_gst").value = price;
    row.querySelector("#amt").value = price +
        price * (Number(row.querySelector("#s_gst").value || 0) + Number(row.querySelector("#c_gst").value || 0));

    calculateTotal();
}

async function fillRow(rowId, item) {
    const row = document.getElementsByTagName("tr")[rowId];

    row.querySelector("#id").value = item?.id || "";
    row.querySelector("#code").value = item?.code || "";
    row.querySelector("#name").value = item?.title || "";
    row.querySelector("#weight").value = item ? row.querySelector("#weight").value || 1 : 0;
    row.querySelector("#s_gst").value = (item?.product_gst_percentage || 0) / 2;
    row.querySelector("#c_gst").value = (item?.product_gst_percentage || 0) / 2;
    row.querySelector("#rate_wo_gst").value = item?.price || 0;

    calculateRow(rowId);
}

async function search(row, name, code = null) {
    if (currentData[code || name])
        return fillRow(row, currentData[code || name]);

    if (!name && !code)
        return fillRow(row);

    [code, name] = [code?.replace("*", ""), name?.replace("-Cleaned", "")]

    const results = await fetch(`/api/products/?${code ? "code" : "search"}=${name || code}`)
        .then((res) => res.json())
        .then((json) => json.results);

    results.forEach((result) => result.can_be_cleaned && results.push({
        ...result, title: `${result.title}-Cleaned`, code: `*${result.code}`, price: result.cleaned_price
    }))

    results.forEach((result) => currentData[result.title] = currentData[result.code] = result);

    const options = results.map((result) => `<option data-id="${result.id}" value="${code ? result.code : result.title}" >`);

    document.getElementById("name_options").innerHTML = options.join("");
}

async function checkout() {
    const trs = document.querySelectorAll("tr");
    const products = [];

    for (let i = INITIAL_ROWS; i < rowCount + INITIAL_ROWS; i++) {
        const row = trs[i];

        const id = Number(row.querySelector("#id").value?.replace("*", ""));
        const weight_qty = Number(row.querySelector("#weight").value);
        const cleaned_status = Number(row.querySelector("#id").value.startsWith("*"));

        if (id && weight_qty)
            products.push({id, quantity: weight_qty, weight: weight_qty, cleaned_status});
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

for (let i = 0; i < 5; i++)
    addRow();


document.getElementById("invoice-form").addEventListener("submit", (e) => {
    e.preventDefault();
    checkout().then();
});
