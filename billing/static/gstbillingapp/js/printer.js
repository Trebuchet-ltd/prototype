const BILL_TABLE =
    `
&nbsp;                                                 
         
<b>                                                 
                    DreamEat
+______________________________________________+
|            Item          | Wgt | Qty | Price |
+----------------------------------------------+
</b><ITEMS><b>
+----------------------------------------------+
|        Total             |      T$$$$$       |
+----------------------------------------------+

Total Payable Amount T$$$$$ Rs
</b>



&nbsp;
`;

const ROW_LENGTH = 48;

const WGT_LENGTH = 6;
const QTY_LENGTH = 6;
const PRICE_LENGTH = 9;

const ITEM_LENGTH = ROW_LENGTH - PRICE_LENGTH - QTY_LENGTH - WGT_LENGTH

function space(count) {
    let spaces = "";
    for (let i = 0; i < Number(count).toFixed(0); i++)
        spaces += "&nbsp;";

    return spaces;
}

function createBillRow({title, weight, quantity, price}) {
    const titles = title.split(new RegExp("(.{"+(ITEM_LENGTH-2)+"})")).filter((s) => s && s!== " ");

    console.log(titles, "titles");

    let col = `|${titles[0]}${titles.length > 1 ? "-" : ""}`
    let row =
        `${col}${space(ITEM_LENGTH - col.length)}` +
        `|${weight}${space(WGT_LENGTH - weight.length - 1)}` +
        `|${quantity}${space(QTY_LENGTH - quantity.length - 1)}` +
        `|${space(PRICE_LENGTH - price.length - 2)}${price}|`

    for (let i = 1; i < titles.length; i++) {
        col = `|${titles[i]}${titles.length - i === 1 ? "" : "-"}`
        row +=
            `\n${col}${space(ITEM_LENGTH - col.length)}|${space(WGT_LENGTH - 1)}` +
            `|${space(QTY_LENGTH - 1)}|${space(PRICE_LENGTH - 2)}|`
    }

    return row;
}

function printBill({total, order_item}) {
    const printWindow = window.open("", "Print Bill");

    const rows = order_item
        .map(({quantity, item}) => ({
            quantity: String(quantity), title: String(item.title), weight: String(item.weight),
            price: String(item.can_be_cleaned ? item.cleaned_price : item.product_rate_with_gst)
        }))
        .map(createBillRow);

    const print = BILL_TABLE.replaceAll("T$$$$$", `${space(6 - String(total).length)}${total}`)
        .replace("<ITEMS>", rows.join("<br>"));

    printWindow.document.write('<html lang="en"><body style="font-family: sans-serif;"><pre>');
    printWindow.document.write(print);
    printWindow.document.write('</pre></body></html>');
    printWindow.document.close();

    printWindow.focus();
    printWindow.print();
}
