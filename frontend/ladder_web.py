"""
Web interface to the wrank commands.
Still statically configured.
Currently broken i think since rearrange of files.
"""

import web
import os
import sys
import json
import urllib

import wrank.front

HEADER = os.path.join(os.path.dirname(__file__),"..", "static", "header.html")
FOOTER = os.path.join(os.path.dirname(__file__),"..", "static", "footer.html")
PART = os.path.join(os.path.dirname(__file__),"..", "static", "part.html")

class index:

    def GET(self):
        web.header('Content-Type','text/html; charset=utf-8', unique=True)

        page = ""
        # header content
        with open(HEADER) as f:
            page += f.read()


        page += """
        <script type="text/javascript">
        function wrank_do_it(command_text)
        {
            function ladder_response(json_response){
                var para = document.createElement("P");
                var pre = document.createElement("PRE");
                para.appendChild(pre);
                jQuery.each(json_response,
                    function(i , line) {
                        pre.appendChild(document.createTextNode(line));
                        pre.appendChild(document.createElement("BR"));
                    }
                );
                jQuery("#LADDER_OUTPUT").prepend(para);
            }

            jQuery.getJSON('wrank?' + jQuery.param({'command':encodeURIComponent(command_text)}), success=ladder_response);
        }
        function command_send_button()
        {
            var textBox = document.getElementById('LADDER_INPUT');
            wrank_do_it(textBox.value)
        }
        wrank_do_it("ladder -vv")
        </script>
        <button id="button" onclick="command_send_button()">send command</button>
        <input type="text" id="LADDER_INPUT">
        <div>
        Output of commands will print below, commands are:<br>
        ladder [-v[v]] (print the ladder with increasing verbosity levels)<br>
        add [player] (add a player) <br>
        game [a b] {beat,lost,draw} [c d] (add a game) <br>
        history [player] (show the game history)<br>
        next [names] (given some players, pick a nice game)<br>
        whowins a b c d (show the probabilities of the game a b vs c d)<br>
        </div>
        <div id="LADDER_OUTPUT">
        </div>
        """

        # footer content
        with open(FOOTER) as f:
            page = page + f.read()

        return page

class LadderController(object):
    """docstring for LadderController"""
    def GET(self):
        user_input = web.input(command='')
        user_command = urllib.unquote(user_input.command)
        print user_command
        ret = k.ladder_command(user_command.split())
        web.header('Content-Type', 'application/json')
        return json.dumps(ret)

if __name__ == "__main__":
    urls = (
        '/', 'index',
        '/wrank', 'LadderController'
    )
    k = wrank.front.LadderManager(sys.argv[2])
    app = web.application(urls, globals())
    app.run()
