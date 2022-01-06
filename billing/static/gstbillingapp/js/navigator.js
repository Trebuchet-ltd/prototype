function rowEventHandler(e) {

    if (!e.key.startsWith("Arrow"))
        return;

    const cId = document.activeElement.id
    const col = document.activeElement.parentElement;
    const row = col.parentElement;

    if (e.key === "ArrowRight")
        col.nextElementSibling?.firstElementChild?.focus();
    else if (e.key === "ArrowLeft")
        col.previousElementSibling?.firstElementChild?.focus();
    else if (e.key === "ArrowDown")
        row.nextElementSibling?.querySelector(`#${cId}`)?.focus();
    else
       row.previousElementSibling?.querySelector(`#${cId}`)?.focus();
}
