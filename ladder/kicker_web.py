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
        Here goeth the text
        </div>
        <script>
        function kicker()
        {
            var textBox = document.getElementById('KICKER_INPUT');
            kicker_text = httpGet('kicker' + textBox.value);
            var para = document.createElement("P");
            var t = document.createTextNode(kicker_text);
            para.appendChild(t);
            document.getElementById("KICKER_OUTPUT").appendChild(para);
        }
        </script>
        """

        with open("www/part.html") as f:
            page = page + f.read()



        # footer content
        with open("static/footer.html") as f:
            page = page + f.read()

        return page

class KickerController(object):
    """docstring for KickerController"""
    def GET(self, text_input):
        k = kicker.KickerManager()
        print text_input.split()
        return "\n<br>".join(k.kicker_command(text_input.split()))




if __name__ == "__main__":
    urls = (
        '/', 'index',
        '/kicker(.*)', 'KickerController'
    )

    app = web.application(urls, globals())
    app.run()