> Represents the connection between the host, the server and the other

The format of a request:

    @from:to kind(key1, key2, key3...)

    identification(login, uuid)
    -> {"kind": "identification", "login": ..., "uuid": ...}

    id = identification

Here's what happens

    @host:server   id(username, uuid)
    @server:host   id state change(state="accepted")
                   id state change(state="refused", reason) && close
    @other:server  new request(by, uuid)
    @server:owner  new request(by)

    @host:server   request state change(state="accepted")
                   request state change(state="refused") && close

    @server:both   select hero(heros=[names...])
    @both:server   hero chosen(hero)

    @server:both   start game()
    @both:server   ready()

    -> loop
    @server:both   game state change(state="going", own=private player state,
                                     other=public player state)
    @both:server   input state change(state=input state)
    -> end loop

    @server:one    game state change(state="won")
    @server:other  game state change(state="lost")

    @server:both   close

