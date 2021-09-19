show_password = (id, span_id) => {
    const text = document.getElementById(id)
    let pass= document.getElementById(id)
    if(pass.type === 'password'){
        pass.type='text';
        document.getElementById(span_id).textContent ='hide';
    }
    else{
        pass.type='password'
        document.getElementById(span_id).textContent='show';
    }

}