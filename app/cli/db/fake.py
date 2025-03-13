"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from app.api.v1.model.book import Book
from app.lin import db


def fake():
    with db.auto_commit():
        # 添加书籍
        book1 = Book()
        book1.title = "深入理解计算机系统"
        book1.author = "Randal E.Bryant"
        book1.summary = """
        从程序员的视角，看计算机系统！\n
        本书适用于那些想要写出更快、更可靠程序的程序员。
        通过掌握程序是如何映射到系统上，以及程序是如何执行的，读者能够更好的理解程序的行为为什么是这样的，以及效率低下是如何造成的。
        粗略来看，计算机系统包括处理器和存储器硬件、编译器、操作系统和网络互连环境。
        而通过程序员的视角，读者可以清晰地明白学习计算机系统的内部工作原理会对他们今后作为计算机科学研究者和工程师的工作有进一步的帮助。
        它还有助于为进一步学习计算机体系结构、操作系统、编译器和网络互连做好准备。\n
        本书的主要论题包括：数据表示、C程序的机器级表示、处理器结构，程序优化、存储器层次结构、链接、异常控制流、虚拟存储器和存储器管理、系统级I/O、网络编程和并发编程。书中所覆盖的内容主要是这些方面是如何影响应用和系统程序员的。
        """
        book1.image = "https://img3.doubanio.com/lpic/s1470003.jpg"
        db.session.add(book1)

        book2 = Book()
        book2.title = "C程序设计语言"
        book2.author = "（美）Brian W. Kernighan"
        book2.summary = """
        在计算机发展的历史上，没有哪一种程序设计语言像C语言这样应用广泛。
        本书原著即为C语言的设计者之一Dennis M.Ritchie和著名计算机科学家Brian W.Kernighan合著的一本介绍C语言的权威经典著作。
        我们现在见到的大量论述C语言程序设计的教材和专著均以此书为蓝本。
        原著第1版中介绍的C语言成为后来广泛使用的C语言版本——标准C的基础。
        人们熟知的“hello,World"程序就是由本书首次引入的，现在，这一程序已经成为众多程序设计语言入门的第一课。\n
        原著第2版根据1987年制定的ANSIC标准做了适当的修订．引入了最新的语言形式，并增加了新的示例，通过简洁的描述、典型的示例，作者全面、系统、准确地讲述了C语言的各个特性以及程序设计的基本方法。
        对于计算机从业人员来说，《C程序设计语言》是一本必读的程序设计语 言方面的参考书。
        """
        book2.image = "https://img3.doubanio.com/lpic/s1106934.jpg"
        db.session.add(book2)
