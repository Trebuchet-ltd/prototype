function rowEventHandler({key}) {

    if (!key.startsWith("Arrow"))
        return;

    const cId = document.activeElement.id
    const col = document.activeElement.parentElement;
    const row = col.parentElement;

    if (key === "ArrowRight" && !col.nextElementSibling?.firstElementChild.disabled)
        col.nextElementSibling?.firstElementChild?.focus();
    else if (key === "ArrowLeft")
        col.previousElementSibling?.firstElementChild?.focus();
    else if (key === "ArrowDown")
        row.nextElementSibling?.querySelector(`#${cId}`)?.focus();
    else
       row.previousElementSibling?.querySelector(`#${cId}`)?.focus();
}
