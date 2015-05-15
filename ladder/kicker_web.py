import web
import kicker

class index:

    def GET(self):
        page = ""
        # header content
        with open("static/header.html") as f:
            page += f.read()


        page += """
        <button id="button" onclick="kicker()">kickify</button>
        <input type="text" id="KICKER_INPUT">
        <div id="KICKER_OUTPUT">
        Here goes the output, try add [player], game [a b] {beat,lost,draw} [c d], next [names], whowins [names]
        WARNING next command is SLOW
        </div>
        <script>
        function kicker()
        {
            var textBox = document.getElementById('KICKER_INPUT');
            kicker_text = httpGet('kicker_' + textBox.value).split("<br>");
            var para = document.createElement("P");
            for (i = 0; i < kicker_text.length; i++){
                para.appendChild(document.createTextNode(kicker_text[i]));
                para.appendChild(document.createElement("BR"));
            }
            document.getElementById("KICKER_OUTPUT").appendChild(para);
        }
        </script>
        """

        with open("part.html") as f:
            page = page + f.read()



        # footer content
        with open("static/footer.html") as f:
            page = page + f.read()

        return page

class KickerController(object):
    """docstring for KickerController"""
    def GET(self, text_input):
        print text_input.split()
        ret = k.kicker_command(text_input.split())
        k.write_index_html()
        return "\n<br>".join(ret)




if __name__ == "__main__":
    urls = (
        '/', 'index',
        '/kicker_(.*)', 'KickerController'
    )
    k = kicker.KickerManager()
    app = web.application(urls, globals())
    app.run()