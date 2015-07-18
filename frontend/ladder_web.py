import web
import os
import json
import urllib

import wrank

HEADER = os.path.join(os.path.dirname(__file__), "static", "header.html")
FOOTER = os.path.join(os.path.dirname(__file__), "static", "footer.html")
PART = os.path.join(os.path.dirname(__file__), "static", "part.html")

class index:

    def GET(self):
        web.header('Content-Type','text/html; charset=utf-8', unique=True)

        page = ""
        # header content
        with open(HEADER) as f:
            page += f.read()


        page += """
        <script type="text/javascript">
        function wrank_do_it()
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
            var textBox = document.getElementById('LADDER_INPUT');
            jQuery.getJSON('wrank?' + jQuery.param({'command':encodeURIComponent(textBox.value)}), success=ladder_response);
        }
        </script>
        <button id="button" onclick="wrank_do_it()">kickify</button>
        <input type="text" id="LADDER_INPUT">
        <div id="LADDER_OUTPUT">
        Here goes the output, commands:<br>
        add [player]<br>
        game [a b] {beat,lost,draw} [c d]<br>
        next [names]<br>
        whowins a b c d<br>
        </div>
        """

        with open(PART) as f:
            page = page + f.read()

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
    k = wrank.LadderManager(os.path.join(os.path.dirname(__file__), "kicker.log"))
    app = web.application(urls, globals())
    app.run()