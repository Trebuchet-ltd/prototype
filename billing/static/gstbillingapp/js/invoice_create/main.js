const INITIAL_ROWS = 7;

let currentData = {};
let rowCount = 0;

function addRow() {
    let row = document.getElementById("invoice_row").content.cloneNode(true);

    const cRow = rowCount++ + INITIAL_ROWS;

    row.querySelector("#sl_no").innerText = rowCount;
    row.querySelector("#code").addEventListener("keyup", (e) => search(cRow, null, e.target.value));
    row.querySelector("#name").addEventListener("keyup", (e) => search(cRow, e.target.value));
    row.querySelector("#quantity").addEventListener("keyup", () => calculateRow(cRow));

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

    row.querySelector("#amt").value = Number(row.querySelector("#rate_wo_gst").value || 0) *
        Number(row.querySelector("#quantity").value || 0);

    calculateTotal();
}

async function fillRow(rowId, item) {
    const row = document.getElementsByTagName("tr")[rowId];

    row.querySelector("#id").value = item?.id || "";
    row.querySelector("#code").value = item?.code || "";
    row.querySelector("#name").value = item?.title || "";
    row.querySelector("#quantity").value = item ? Number(row.querySelector("#quantity").value) || 1 : 0;
    row.querySelector("#s_gst").value = (item?.gst_percent || 0);
    row.querySelector("#rate_wo_gst").value = item?.price || 0;

    calculateRow(rowId);

    if (item && INITIAL_ROWS + rowCount - rowId <= 2)
        addRow();

}

async function search(row, name, code = null) {
    if (currentData[code || name])
        return fillRow(row, currentData[code || name]);

    if (!name && !code)
        return fillRow(row);

    [code, name] = [code?.replace("*", ""), name?.replace("-Cleaned", "")]

    const results = await fetch(`/bill/bill_products?${code ? "code" : "title"}=${name || code}`)
        .then((res) => res.json())
        .then((json) => json.results);

    results.forEach((result) => result.can_be_cleaned && results.push({
        ...result, title: `${result.title}-Cleaned`, code: `*${result.code}`, price: result.cleaned_price
    }))

    results.forEach((result) => currentData[result.title] = currentData[result.code] = result);

    const options = results.map((result) => `<option data-id="${result.id}" value="${code ? result.code : result.title}" >`);

    document.getElementById(name ? "name_options" : "code_options").innerHTML = options.join("");
}

async function checkout() {
    const trs = document.querySelectorAll("tr");
    const products = [];
    const names = {};

    for (let i = INITIAL_ROWS; i < rowCount + INITIAL_ROWS; i++) {
        const row = trs[i];

        const name = row.querySelector("#name").value;
        const id = Number(row.querySelector("#id").value?.replace("*", ""));
        const quantity = Number(row.querySelector("#quantity").value);
        const cleaned_status = row.querySelector("#code").value.startsWith("*");
        const price = row.querySelector("#rate_wo_gst").value

        if (!id || !quantity || !name)
            continue;

        if (name in names) {
            if (window.confirm(`Merge Duplicate entry for ${name} ?`))
                products[names[name]] = {...products[names[name]], quantity: quantity + products[names[name]].quantity};

            continue;
        }

        names[name] = products.push({id, quantity, cleaned_status, price}) - 1;
    }

    if (products.length === 0)
        return window.alert("Fill the form !!!");

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
                    gst: document.getElementById("customer-gst-input").value,
                    type: document.getElementById("invoice_type").value,
                    products
                }
            )
        }).then((res) => res.json())

    const {bill} = await fetch(`/bill/get/${await order.id}`).then((res) => res.json());

    const printer = window.open("", "_blank");

    printer.document.write(`<pre>${ bill }</pre>`);
    printer.document.close();

    printer.focus();
    printer.print();

    // printBill(await order.json());
}

for (let i = 0; i < 3; i++)
    addRow();


document.getElementById("invoice-form").addEventListener("submit", (e) => {
    e.preventDefault();
    checkout().then();
});
