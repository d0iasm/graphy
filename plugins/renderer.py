import boto3
import datetime
import graphviz
import os

# from . import parser
import parser


class Renderer(object):
    """Image renderer from natural language. """
    def __init__(self, new_text):
        self.dot = graphviz.Graph(format='png', engine='neato',
                                  edge_attr={'color': 'white', 'fontsize': '14', 'len': '2'},
                                  graph_attr={'overlap': 'false', 'bgcolor': '#343434',
                                              'fontcolor': 'white', 'style': 'filled',},
                                  node_attr={'fixedsize': 'true', 'style': 'solid,filled',
                                             'color': 'black', 'shape': 'circle', 'colorscheme': 'gnbu5',
                                             'fontcolor': 'black', 'fontsize': '16'})
        self.parser = parser.Parser()
        self.new = new_text
        # TODO: Bucket policy
        self.session = boto3.session.Session(aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                                             aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                                             region_name='ap-northeast-1')
        self.s3 = self.session.resource('s3')
        self.s3_bucket = os.environ['S3_BUCKET_NAME']

        
    def add_edges(self):
        """
        :param string line: a natural language text for parsing.
        """
        for child, parent in self.parser.find_parent_child():
            self.dot.edge(child, parent)
            
        
    def add_nodes(self):
        """
        :param string line: a natural language text for parsing.
        """
        for node in self.parser.find_nodes():
            self.dot.node(node[0], label=node[0], **node[1])

            
    def copy(self):
        self.s3.Object(self.s3_bucket, 'old').copy_from(
            CopySource={'Bucket': self.s3_bucket, 'Key': 'new'})

        
    def render(self, text):
        self.parser.set(text)
        self.add_nodes()
        self.add_edges()
        name = 'results/result_' + datetime.datetime.now().strftime('%s') + '.png'
        print("[Debug] dot file content: " + self.dot.source)
        self.s3.Object(self.s3_bucket, name).put(
            Body=graphviz.Source(self.dot.source, engine='neato', format='png').pipe())
        return name, text

    
    def reset(self):
        self.s3.Object(self.s3_bucket, 'old').copy_from(
            CopySource={'Bucket': self.s3_bucket, 'Key': 'empty'})
        self.s3.Object(self.s3_bucket, 'new').copy_from(
            CopySource={'Bucket': self.s3_bucket, 'Key': 'empty'})

        
    def merge(self):
        old_text = self.s3.Object(
            self.s3_bucket, 'old').get()['Body'].read().decode('utf-8')

        return (old_text + self.new).strip()

    
    def save(self, text):
        self.s3.Object(self.s3_bucket, 'new').put(Body=text)

        
    def debug(self, text):
        self.parser.set(text)
        self.add_nodes()
        self.add_edges()
        print(self.dot.source)
        self.dot.render('debug', view=True, cleanup=True)


if __name__ == '__main__':
    line = """町というのはちいちゃくって、城壁がこう町全体をぐるっと回ってて、それが城壁の上を歩いても１時間ぐらいですよね。１時間かからないぐらいだね。４、５０分で。そうそう。
ほいでさあ、ずっと歩いていたんだけど、そうすと上から、なんか町の中が見れるじゃん。
あるよね。
ほいでさあ、なんか途中でワンちゃんに会ったんだね。
散歩をしてるワンちゃんに会ったんだ。
城壁の上をやっぱ観光客なんだけどワンちゃん連れてきてる人たち結構多くて。
で、こう、そのワンちゃんと２人を、なに、お父さんとお母さんと歩いて、ワンちゃんに会ったんだ。
途中で。ワンちゃーんとか言ってなでて、ほいで、この人たちはこっち行って、あたしらこっち行ったじゃん。
ずうーとこうやって回ってきてるの。
また会っちゃって。
ここで。
そうしたら。
おー、そら地球はやっぱり丸かったみたいだね。　
そうしたらそのワンちゃんがなんかか喜んじゃって、で、あたしの方に走ってきて、とびついてきちゃってさ。
別にあたしさあ、別にさっきなでただけなのにさあ、なんかすごーいなつかれちゃってね。　
さっきね、別に、そんなになでてもいないんだよ。
よしよしって言っただけなのに。
あらワンちゃんだーとか言ってすれ違ったんだよ。
普通に。
それでその次のとき、向こうの方からはーっといってかけてくるじゃん。
すごい勢いで走って。
私、あ、あーさっきの犬だとか私たちが言っとるじゃん。
あんで向こうの人たちも、あっ、さっき会った子たちねみたいな感じで気がついたじゃん。
犬も気がついたじゃん。
じゃははって走ってきちゃって、犬が。
そうなんだ。"""
    print(len(line))
    r = Renderer(line)
    r.debug(line)
