# Graph Extraction Project

## Основная информация

Все файлы расширения .tex, графы по которым необходимо построить, должны находиться в директории source_files.

При запуске main.py в директории extracted_information для каждого tex-файла создается папка. В этой папке создаются следующие файлы:
 — graph.json содержит граф в виде списка смежности. Этот файл нужен для дальнейшей работы с графом.
 — graph_properties.json содержит базовую информацию о степенях вершин графа.
 — visualization.html хранит изображение графа. Неоюходимо открывать этот файл в браузере

При повторном запуске main.py вся информация для файлов, находящихся в source_files будет перезаписана.

После запуска main.py можно начинать работу с извлеченным графом. В файле "analyzation_script.py" в качестве file_path надо указать точный путь до файла graph.json, с которым предстоит работа. Далее необходимо создать экземпляр класса Graph, он получит представление графа из заданного graph.json файла. У класса Graph пока реализован один метод - get_parents, который принимает как параметр полное название элемента element_name и создает в папке, относящейся к этому графу (в extracted_information), визуализацию подграфа, содержащего только все вершины, из которой достижим element_name.

Так как у tex-файлов нет общей структуры и пользователи могут использовать многообразный синтаксис для выделения блоков в тексте, невозможно с точностью покрыть все команды и аргументы команд в парсере, поэтому в скрипте main.py можно добавлять дополнительные команды или названия блоков, которые будут добавлены в регулярные выражения для поиска. 

## Визуализация графа

У графа в html-визуалиации может быть несколько цветов вершин:
— Красный - в зависимостях есть цикл
— Зеленый - формулировки данного элемента нет в этом tex-файле
— Оранжевый - данный элемент относится к цитированию источника
