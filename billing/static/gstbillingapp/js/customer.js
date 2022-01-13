const names = document.getElementById("user_name_options");
const phones = document.getElementById("user_phone_options");

const option = (key, value) => `<option data-id="${key}" value="${value}">`;

const database = {};

async function searchUser(name, mob = "") {
    const {results} = await fetch(`/auth/users/?first_name=${name}&username=${mob}`)
        .then((res) => res.json());

    names.innerHTML = results.map(({first_name, id}) => `<option data-id="${id}" value="${first_name}">`).join("");
    phones.innerHTML = results.map(({username, id}) => `<option data-id="${id}" value="${username}">`).join("");

    results.forEach(({id, first_name, username, Addresses}) => database[id] = {first_name, username, Addresses})
}

async function fillUser(input)
{
    const id = document.querySelector(`option[value="${input}"]`)?.getAttribute("data-id");

    if(!id || !database[id])
        return;

    name.value = database[id].first_name;
    phone.value = database[id].username;
    address.value = database[id].Addresses[0].address;
    pin.value = database[id].Addresses[0].pincode;
    gst.value = database[id].Addresses[0].gst || "";
}


const name = document.getElementById("customer-name-input");
const phone = document.getElementById("customer-phone-input");
const address = document.getElementById("customer-address-input");
const pin = document.getElementById("customer-pin-input");
const gst = document.getElementById("customer-gst-input");

name.onkeyup = (e) => e.key !== "Enter" && searchUser(e.target.value);
phone.onkeyup = (e) => e.key !== "Enter" && searchUser("", e.target.value);

name.onchange = (e) => fillUser(e.target.value);
phone.onchange = (e) => fillUser(e.target.value);
