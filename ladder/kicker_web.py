import web
import os
import json

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
                for (i = 0; i < json_response.length; i++){
                    pre.appendChild(document.createTextNode(json_response[i]));
                    pre.appendChild(document.createElement("BR"));
                }
                document.getElementById("KICKER_OUTPUT").appendChild(para);
            }
            var textBox = document.getElementById('KICKER_INPUT');
            httpGet('kicker_' + encodeURIComponent(textBox.value), updateKicker);
        }
        </script>
        <button id="button" onclick="kicker()">kickify</button>
        <input type="text" id="KICKER_INPUT">
        <div id="KICKER_OUTPUT">
        Here goes the output, try add [player], game [a b] {beat,lost,draw} [c d], next [names], whowins [names]
        WARNING next command is SLOW
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
    def GET(self, text_input):
        print text_input.split()
        ret = k.kicker_command(text_input.split())
        web.header('Content-Type', 'application/json')
        return json.dumps(ret)

if __name__ == "__main__":
    urls = (
        '/', 'index',
        '/kicker_(.*)', 'KickerController'
    )
    k = kicker.KickerManager()
    app = web.application(urls, globals())
    app.run()