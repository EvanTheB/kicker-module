import web
import os
import json
import urllib

import kicker

HEADER = os.path.join(os.path.dirname(__file__), "static", "header.html")
FOOTER = os.path.join(os.path.dirname(__file__), "static", "footer.html")

class index:

    def GET(self):
        web.header('Content-Type','text/html; charset=utf-8', unique=True)

        page = ""
        # header content
        with open(HEADER) as f:
            page += f.read()


        page += """
        <script type="text/javascript">
        function kicker()
        {
            function updateKicker(json_response){
                var para = document.createElement("P");
                var pre = document.createElement("PRE");
                para.appendChild(pre);
                jQuery.each(json_response,
                    function(i , line) {
                        pre.appendChild(document.createTextNode(line));
                        pre.appendChild(document.createElement("BR"));
                    }
                );
                jQuery("#KICKER_OUTPUT").prepend(para);
            }
            var textBox = document.getElementById('KICKER_INPUT');
            jQuery.getJSON('kicker?' + jQuery.param({'command':encodeURIComponent(textBox.value)}), success=updateKicker);
        }
        </script>
        <button id="button" onclick="kicker()">kickify</button>
        <input type="text" id="KICKER_INPUT">
        <div id="KICKER_OUTPUT">
        Here goes the output, commands:<br>
        add [player]<br>
        game [a b] {beat,lost,draw} [c d]<br>
        next [names]<br>
        whowins a b c d<br>
        </div>
        """

        with open(kicker.PART_HTML) as f:
            page = page + f.read()

        # footer content
        with open(FOOTER) as f:
            page = page + f.read()

        return page

class KickerController(object):
    """docstring for KickerController"""
    def GET(self):
        user_input = web.input(command='')
        user_command = urllib.unquote(user_input.command)
        print user_command
        ret = k.kicker_command(user_command.split())
        web.header('Content-Type', 'application/json')
        return json.dumps(ret)

if __name__ == "__main__":
    urls = (
        '/', 'index',
        '/kicker', 'KickerController'
    )
    k = kicker.KickerManager()
    app = web.application(urls, globals())
    app.run()