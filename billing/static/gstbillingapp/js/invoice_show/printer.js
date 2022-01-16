const BILL_TABLE =
    `
<b>                                                 
                  DreamEat</b>
     7/145 Arakkathazathu, Mulamthuruthy        
     Arakunnam, Ernakulam, Kerala, 682313
              GST 32CRAPA9979B1ZZ
<b>              
+______________________________________________+
| Sl |            Item           | Qty | Price |
+----------------------------------------------+
</b><ITEMS><b>
+----------------------------------------------+
|        Total             |      T$$$$$       |
+----------------------------------------------+

Total Payable Amount T$$$$$ Rs

<USER>
<ADDRESS>
<GST>
</b>



&nbsp
`;

const ROW_LENGTH = 48;

const SL_LENGTH = 5;
const QTY_LENGTH = 6;
const PRICE_LENGTH = 9;

const ITEM_LENGTH = ROW_LENGTH - PRICE_LENGTH - QTY_LENGTH - SL_LENGTH

function space(count) {
    let spaces = "";
    for (let i = 0; i < Math.floor(Number(count)); i++)
        spaces += "&nbsp;";

    return spaces;
}

function createBillRow({title, quantity, price, sl}) {
    const titles = title.split(new RegExp("(.{"+(ITEM_LENGTH-2)+"})")).filter((s) => s && s!== " ");

    let col = `|${titles[0]}${titles.length > 1 ? "-" : ""}`
    let row =
        `|${sl}${space(SL_LENGTH - sl.length-1)}`+
        `${col}${space(ITEM_LENGTH - col.length)}` +
        `|${quantity}${space(QTY_LENGTH - quantity.length - 1)}` +
        `|${space(PRICE_LENGTH - price.length - 2)}${price}|`

    for (let i = 1; i < titles.length; i++) {
        col = `|${titles[i]}${titles.length - i === 1 ? "" : "-"}`
        row +=
            `<br>|${space(SL_LENGTH - 1)}${col}${space(ITEM_LENGTH - col.length)}` +
            `|${space(QTY_LENGTH - 1)}|${space(PRICE_LENGTH - 2)}|`
    }

    return row;
}

function printBill({total, order_item, address}) {
    const printWindow = window.open("", "_blank");

    const rows = order_item
        .map(({quantity, item, is_cleaned, type_of_quantity}, i) => ({
            quantity: String(quantity),
            price: String((is_cleaned ? item.cleaned_price : item.price) * item.weight  * quantity),
            title: String(`${item.title}${is_cleaned ? " Cleaned": ""}`),
            sl: String(i+1)
        }))
        .map(createBillRow);

    const print = BILL_TABLE
        .replace("<USER>", address.name)
        .replace("<ADDRESS>", address.address)
        .replace("<GST>", address.gst ? `GST No : ${address.gst}` : "")
        .replace("<ITEMS>", rows.join("<br>"))
        .replaceAll("T$$$$$", `${space(6 - String(total).length)}${total}`)
        .replaceAll("\n", "<br>");

    printWindow.document.write('<html lang="en"><body style="font-family: sans-serif;"><pre>');
    printWindow.document.write(print);
    printWindow.document.write('</pre></body></html>');
    printWindow.document.close();

    printWindow.focus();
    printWindow.print();
}
