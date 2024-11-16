from flet import (AppBar,Page,View,ThemeMode,Theme,Column,Container,Row,app,Text,TextField,ElevatedButton,AlertDialog,TextButton,
    Image,Divider,ListView,colors,RoundedRectangleBorder,TextOverflow,ButtonStyle,icons,MainAxisAlignment,alignment,padding,CrossAxisAlignment,FontWeight,
    ImageFit,TextAlign,SnackBar,Icon,border_radius,BoxShadow,Offset,ControlState,ImageRepeat)

from ui_components import create_elevated_button,get_text_size
from data_manager import (
    load_contacts_by_service,
    load_inspectors_by_cycle,
    save_state,
    load_state,
    update_data_if_online,
    load_data,)
import sys
from threading import Lock
import logging # journalisation 
#__Configuration de logging
format="%(asctime)s.%(msecs)03d--%(levelname)s : %(message)s"
logging.basicConfig(format="%(message)s", level=logging.ERROR)
contact_dialog = None
def main(page: Page):
    page.title = "Phone Galerie"
    saved_route = load_state()
    page.route = saved_route if saved_route == "/" else "/" 
    page.theme_mode = ThemeMode.LIGHT
    page.fonts = {"4_3D": "fonts/4_3D.ttf",}
    page.theme = Theme(font_family="4_3D")
    page.window.width = 520
    page.window.height = 850
    page.bgcolor = '#ffd966'
    page.horizontal_alignment='center'
    page.vertical_alignment='center'
    logging.info(f"Initial route:{page.route}")    
    page.horizontal_alignment = 'center'
    page.vertical_alignment = 'center'
    page.scroll = 'true'

    contacts_list = ListView(expand=True)
    global contact_dialog
    contact_dialog = AlertDialog(
        title=Text("", text_align=TextAlign.CENTER),
        actions=[
            Column([
                TextButton("Appeler", icon=icons.ADD_CALL),
                TextButton(
                    content=Row([Image(src="assets/wtsp.png", height=24, width=24), Text("WhatsApp")]),
                ),
                TextButton("Copier le numéro", icon=icons.CONTENT_COPY),
            ], spacing=0),
            TextButton("Fermer", on_click=lambda _: close_dialog())
        ],
    )
    page.overlay.append(contact_dialog)
    # Search Bloc ================================================================================================
    def update_contact_dialog_actions(contact_info):
        """Met à jour les actions du dialogue pour le contact sélectionné."""
        phone_number = str(contact_info['mobile'])
        contact_dialog.actions[0].controls[0].on_click = lambda _: page.launch_url(f"tel:{phone_number}")
        contact_dialog.actions[0].controls[1].on_click = lambda _: page.launch_url(f"https://wa.me/212{phone_number[1:]}")
        contact_dialog.actions[0].controls[2].on_click = lambda _: page.set_clipboard(phone_number)
    def show_school_contacts(sheet_name, icon_name, icon_color, view_title, view_bgcolor):
        global current_contacts_data
        contacts_list.controls.clear()
        current_contacts_data = load_data(sheet_name)
        def update_contact_list(search_value=""):
            """
            Met à jour la liste des établissements en fonction de la valeur de recherche.
            """
            search_value = search_value.strip()

            filtered_contacts = [
                contact for contact in current_contacts_data
                if search_value in contact.get('etab', '') or
                search_value in str(contact.get('mobile', '')) or
                search_value in contact.get('nom', '')  # Recherche par nom du directeur
            ]

            contacts_list.controls.clear()

            if not filtered_contacts:
                # Afficher un message indiquant que les résultats sont vides
                contacts_list.controls.append(
                    Container(
                        content=Text(
                            "لا توجد نتائج مطابقة",
                            size=20,
                            color=colors.RED,
                            text_align=TextAlign.CENTER
                        ),
                        alignment=alignment.center,
                        expand=True
                    )
                )
            else:
                for contact in filtered_contacts:
                    etab = contact.get('etab', 'Établissement Inconnu')
                    nom = contact.get('nom', 'Directeur Inconnu')
                    mobile = contact.get('mobile', 'Non Disponible')

                    contact_row = Container(
                        content=Row(
                            controls=[
                                Column(
                                    controls=[
                                        Text(
                                            etab,
                                            size=20,
                                            weight=FontWeight.BOLD,
                                            color=colors.GREEN if search_value else colors.BLACK,
                                            text_align=TextAlign.RIGHT,
                                            rtl=True
                                        ),
                                        Text(
                                            f"Directeur: {nom}",
                                            size=16,
                                            color=colors.BLACK54,
                                            text_align=TextAlign.RIGHT,
                                            rtl=True
                                        )
                                    ],
                                    spacing=4,
                                    alignment=MainAxisAlignment.CENTER,
                                    horizontal_alignment=CrossAxisAlignment.END,
                                ),
                                Icon(icon_name, color=icon_color)
                            ],
                            alignment=MainAxisAlignment.END,
                            spacing=10
                        ),
                        on_click=lambda e, nom=nom, mobile=mobile: show_school_contact_options(nom, mobile)
                    )

                    contacts_list.controls.append(contact_row)
                    contacts_list.controls.append(Divider(height=1, thickness=1, color="grey"))

            page.update()

        # Initialiser la liste sans filtre
        if current_contacts_data:
            update_contact_list()
        else:
            # Aucune donnée disponible, mais la vue est toujours affichée
            contacts_list.controls.append(
                Container(
                    content=Text(
                        "الرجاء تحديث البيانات للاستمرار",
                        size=20,
                        color=colors.RED,
                        text_align=TextAlign.CENTER
                    ),
                    alignment=alignment.center,
                    expand=True
                )
            )

        # Champ de recherche
        search_field = TextField(
            label="البحث...",
            width=300,
            height=45,
            icon=icons.SEARCH,
            text_align=TextAlign.RIGHT,
            rtl=True,
            on_change=lambda e: update_contact_list(e.control.value)
        )

        # Créer la vue principale
        view = View(
            f"/direction/{sheet_name}",
            [
                AppBar(
                    bgcolor=colors.BLUE_600,
                    title=Text(view_title, color='white', size=24),
                    center_title=True,
                    toolbar_height=55,
                    automatically_imply_leading=True
                ),
                Row(controls=[search_field], alignment=MainAxisAlignment.CENTER),
                contacts_list
            ]
        )
        view.bgcolor = view_bgcolor
        view.horizontal_alignment = 'center'
        view.vertical_alignment = 'center'
        page.views.append(view)
        page.update()
    # utiliser dans inspector et services views
    def show_contact_options(contact_name, sheet_name):
            global contact_dialog
            if contact_dialog is not None and contact_dialog.open:
                # Si le contact est déjà sélectionné, ne rien faire
                if contact_dialog.title.value == f"Options pour {contact_name}":
                    return
                close_dialog()
            data = load_data(sheet_name)
            contact_info = next((item for item in data if item['Nom'] == contact_name), None)
            if contact_info:
                contact_dialog.title.value = f"Options pour {contact_name}"
                update_contact_dialog_actions(contact_info)  # Update actions dynamically
                contact_dialog.open = True
                page.update()
    def close_dialog():
        global contact_dialog
        if contact_dialog is not None:
            contact_dialog.open = False
        page.update()
    def show_school_contact_options(contact_name, mobile):
        """Ouvre la boîte de dialogue avec les options pour un établissement spécifique."""
        global contact_dialog
        if contact_dialog is not None and contact_dialog.open:
            if contact_dialog.title.value == f"Options pour {contact_name}":
                return
            close_dialog()
        contact_dialog.title.value = f"Options pour {contact_name}"
        contact_dialog.open = True
        update_school_contact_dialog_actions({"mobile": mobile})
        page.update()
    def update_school_contact_dialog_actions(contact_info):
        """Met à jour les actions de la boîte de dialogue avec les options de contact pour un établissement spécifique."""
        phone_number = str(contact_info['mobile'])
        contact_dialog.actions[0].controls[0].on_click = lambda _: page.launch_url(f"tel:{phone_number}")
        contact_dialog.actions[0].controls[1].on_click = lambda _: page.launch_url(f"https://wa.me/212{phone_number}")
        contact_dialog.actions[0].controls[2].on_click = lambda _: page.set_clipboard(phone_number)

    def create_inspector_view(page, route, inspectors_data, title, view_bgcolor, button_bgcolor):
        screen_width = page.window.width

        # Créez une liste de boutons stylisés pour chaque inspecteur
        inspector_controls = []
        for inspector in inspectors_data:
            inspector_name = inspector['Nom']
            inspector_button = ElevatedButton(
                content=Row(
                    controls=[
                        # Nom de l'inspecteur avec style et alignement
                        Text(
                            inspector_name,
                            size=18 if screen_width < 500 else 20,  # Ajuste la taille de police pour les petits écrans
                            weight=FontWeight.BOLD,
                            color=colors.BLACK,
                            overflow=TextOverflow.ELLIPSIS,
                            text_align=TextAlign.RIGHT
                        ),
                        # Icône de contact à droite
                        Icon(icons.CONTACT_MAIL, color=colors.WHITE)
                    ],
                    alignment=MainAxisAlignment.END,  # Alignement des éléments du Row à droite
                    spacing=10,
                    expand=True
                ),
                # Taille responsive du bouton en fonction de la largeur de l'écran
                width=360 if screen_width > 500 else 300,
                height=65 if screen_width > 500 else 55,
                # Utilisation de la couleur de fond spécifique pour le bouton
                bgcolor=button_bgcolor,
                on_click=lambda e, name=inspector_name: show_contact_options(name, "inspectors"),
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=12),
                    padding=padding.symmetric(horizontal=16, vertical=10),
                    elevation=6
                )
            )
            inspector_controls.append(inspector_button)
            # Ajouter un diviseur pour séparer chaque inspecteur
            inspector_controls.append(Divider(height=1, thickness=1, color="grey"))

        # Construire la vue avec les boutons des inspecteurs
        view = View(
            route,
            [
                AppBar(
                    bgcolor=colors.BLUE,
                    title=Text(title, rtl=True, color='white', size=24 if screen_width > 500 else 18),
                    center_title=True,
                    automatically_imply_leading=True,
                ),
                Container(height=20),
                # Container principal avec la colonne de boutons d’inspecteurs
                Container(
                    padding=padding.all(16),
                    alignment=alignment.center,  # Centre la colonne dans le conteneur
                    content=Column(
                        controls=inspector_controls,
                        alignment=MainAxisAlignment.CENTER,  # Centre les boutons dans la colonne
                        horizontal_alignment=CrossAxisAlignment.CENTER,  # Centre horizontalement
                        spacing=10
                    )
                )
            ],
            scroll='auto'  # Permet le défilement si la liste dépasse la hauteur de l'écran
        )

        # Configuration de l'arrière-plan et alignement de la vue
        view.bgcolor = view_bgcolor
        view.horizontal_alignment = 'center'
        view.vertical_alignment = 'center'
        page.views.append(view)
        page.update()
    def create_service_view(page, route, service_data, title, view_bgcolor, button_bgcolor):
        screen_width = page.window.width

        # Créer des contrôles pour chaque contact dans le service
        service_controls = []
        for item in service_data:
            item_name = item['Nom']
            
            # Créer un bouton pour chaque contact avec style et alignement
            item_button = ElevatedButton(
                content=Row(
                    controls=[
                        Text(
                            item_name,
                            size=18 if screen_width < 500 else 20,
                            weight=FontWeight.BOLD,
                            color=colors.WHITE,
                            overflow=TextOverflow.ELLIPSIS,
                            text_align=TextAlign.RIGHT
                        ),
                        Icon(icons.CONTACT_MAIL, color=colors.WHITE)
                    ],
                    alignment=MainAxisAlignment.END,
                    spacing=10,
                    expand=True
                ),
                width=360 if screen_width > 500 else 320,  # Largeur responsive
                height=65 if screen_width > 500 else 55,
                bgcolor=button_bgcolor,
                on_click=lambda e, name=item_name: show_contact_options(name, 'services'),
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=12),
                    padding=padding.symmetric(horizontal=16, vertical=10),
                    elevation=6
                )
            )
            service_controls.append(item_button)
            service_controls.append(Divider(height=1, thickness=1, color="grey"))  # Diviseur entre chaque contact

        # Organiser tous les contacts dans une `Column` unique, un par ligne
        view = View(
            route,
            [
                AppBar(
                    bgcolor=colors.BLUE,
                    title=Text(title, rtl=True, color='white', size=24 if screen_width > 500 else 18),
                    center_title=True,
                    automatically_imply_leading=True,
                ),
                Container(height=20),
                Container(
                    padding=padding.all(16),
                    alignment=alignment.center,
                    content=Column(
                        controls=service_controls,
                        alignment=MainAxisAlignment.CENTER,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=10
                    )
                )
            ],
            scroll='auto'
        )

        view.bgcolor = view_bgcolor
        view.horizontal_alignment = 'center'
        view.vertical_alignment = 'center'
        page.views.append(view)
        page.update()

    def show_directeur_view(page):
        """
        Affiche la vue du directeur avec une carte centralisée et des boutons alignés sous la carte.
        """
        directeur_data = load_contacts_by_service("directeur")
        if not directeur_data:
            page.snack_bar = SnackBar(Text("Les données ne sont pas disponibles. Mettez à jour votre base de données."))
            page.snack_bar.open = True
            page.update()
            return

        directeur = directeur_data[0]  # Suppose qu'il y a un seul directeur dans le service "directeur".
        nom = directeur.get("Nom", "غير متوفر")
        mobile = directeur.get("mobile", "غير متوفر")
        role = "المدير الإقليمي لمديرية الحسيمة"

        # Responsiveness: Calcul des tailles en fonction de la largeur de l'écran
        screen_width = page.window.width
        card_width = 0.8 * screen_width if screen_width > 500 else 0.9 * screen_width
        button_width = (card_width - 20) / 3  # Boutons alignés horizontalement avec espacement
        button_height = 50 if screen_width > 500 else 45
        font_size_title = 26 if screen_width > 500 else 22
        font_size_role = 20 if screen_width > 500 else 18

        view = View(
            "/direction/directeur",
            [
                AppBar(
                    bgcolor=colors.BLUE_600,
                    title=Text("المدير الإقليمي", color=colors.WHITE, size=24),
                    center_title=True,
                    toolbar_height=55,
                    automatically_imply_leading=True,
                ),
                # Conteneur principal pour tout centrer
                Column(
                    alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    expand=True,
                    controls=[
                        # Espace flexible en haut
                        Container(height=40),
                        # Carte du directeur
                        Container(
                            width=card_width,
                            padding=padding.all(20),
                            bgcolor=colors.WHITE,
                            border_radius=border_radius.all(20),
                            shadow=BoxShadow(blur_radius=15, color=colors.BLACK12, offset=Offset(0, 4)),
                            content=Column(
                                alignment=MainAxisAlignment.CENTER,
                                horizontal_alignment=CrossAxisAlignment.CENTER,
                                controls=[
                                    Image(
                                        src="assets/manager.png",
                                        width=100,
                                        height=120,
                                        fit=ImageFit.COVER,
                                        border_radius=border_radius.all(60),
                                    ),
                                    Text(
                                        f"السيد {nom}",
                                        size=font_size_title,
                                        weight=FontWeight.BOLD,
                                        rtl=True,
                                        text_align=TextAlign.CENTER,
                                    ),
                                    Text(
                                        role,
                                        size=font_size_role,
                                        rtl=True,
                                        text_align=TextAlign.CENTER,
                                        color=colors.BLACK87,
                                    ),
                                ],
                            ),
                        ),
                        Container(height=20),
                        # Boutons alignés sous la carte
Container(
    padding=padding.symmetric(horizontal=16),  # Ajout du padding ici
    content=Row(
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        controls=[
            ElevatedButton(
                content=Row(
                    controls=[
                        Icon(icons.PHONE, color=colors.WHITE, size=18),
                        Text("اتصال", rtl=True, color=colors.WHITE, size=18),
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    spacing=4,
                ),
                on_click=lambda _: page.launch_url(f"tel:{mobile}"),
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=25),
                    padding=padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=colors.BLUE,
                ),
                width=button_width,
                height=button_height,
            ),
            ElevatedButton(
                content=Row(
                    controls=[
                        Image(
                            src="assets/wtsp.png",
                            width=22,
                            height=22,
                            fit=ImageFit.CONTAIN,
                        ),
                        Text("واتساب", rtl=True, color=colors.WHITE, size=18),
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    spacing=4,
                ),
                on_click=lambda _: page.launch_url(f"https://wa.me/212{mobile[1:]}"),
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=25),
                    padding=padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=colors.GREEN,
                ),
                width=button_width,
                height=button_height,
            ),
            ElevatedButton(
                content=Row(
                    controls=[
                        Icon(icons.COPY, color=colors.WHITE, size=18),
                        Text("نسخ", rtl=True, color=colors.WHITE, size=18),
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    spacing=4,
                ),
                on_click=lambda _: page.set_clipboard(mobile),
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=25),
                    padding=padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=colors.AMBER,
                ),
                width=button_width,
                height=button_height,
            ),
        ],
    ),
)

                        ,
                        # Espace flexible en bas
                        Container(height=40),
                    ],
                ),
            ],
            scroll="auto",
        )

        view.bgcolor = colors.GREY_100
        page.views.append(view)
        page.update()



    def route_change(e):
        global current_contacts_data
        app_bar_height = 55
        current_contacts_data = []
        contacts_list.controls.clear()
        page.update()
        if e is not None:
            page.route = e.route
            logging.info(f"Route change: {e.route}")
            save_state(page.route)
        if page.views and page.views[-1].route == page.route:
            logging.info("La vue demandée est déjà en haut de la pile.")
            return
        if page.route == "/":
            page.views.clear()
            screen_width = page.window.width
            text_size = get_text_size(screen_width)

            # Couleurs pour les différents boutons
            BUTTON_COLORS = {
                'مصالح المديرية': colors.BLUE,
                'أطر التفتيش والتوجيه': colors.DEEP_PURPLE,
                'التعليم الإبتدائي': colors.GREEN,
                'الثانوي الإعدادي': colors.ORANGE,
                'الثانوي التأهيلي': colors.CYAN,
            }
            update_container = Column(
                            controls=[
                                ElevatedButton(
                                    content=Row(
                                        controls=[
                                            Icon(icons.REFRESH, color=colors.WHITE),
                                            Text('تحديث البيانات', rtl=True, size=26,weight=FontWeight.BOLD, overflow=TextOverflow.ELLIPSIS)],alignment=MainAxisAlignment.CENTER),
                                    width=300,height=50,style=ButtonStyle(color=colors.WHITE,bgcolor={ControlState.DEFAULT: colors.INDIGO, ControlState.PRESSED: colors.INDIGO_ACCENT},
                                        shape=RoundedRectangleBorder(radius=8),elevation=5),on_click=lambda _: update_data_if_online(page, update_container)),],alignment=MainAxisAlignment.CENTER)
            view = View(
                "/",
                [
                    Column(
                        controls=[
                            # Logo Image Container at the top
                            Container(
                                content=Image(
                                    src="assets/log.png",
                                    width=350,
                                    height=100,
                                    fit=ImageFit.CONTAIN,
                                    repeat=ImageRepeat.NO_REPEAT,
                                    border_radius=border_radius.all(10),
                                ),
                                alignment=alignment.center
                            ),
                            # Container pour le titre
                            Container(
                                content=Text(
                                    "الدليل الهاتفي للمديرية الإقليمية الحسيمة",
                                    color=colors.BLACK87,  # Texte en noir pour un aspect professionnel
                                    size=30 if screen_width > 500 else 24,
                                    weight=FontWeight.BOLD,
                                    rtl=True,
                                    text_align="center",
                                    font_family="4_3D",
                                ),
                                alignment=alignment.center,
                                padding=padding.symmetric(horizontal=0, vertical=10),
                                bgcolor=colors.BLUE_GREY_50, 
                                border_radius=border_radius.all(0),
                            ),
                            Container(height=20),
                            # Boutons principaux
                            create_elevated_button(
                                'مصالح المديرية',
                                width=360 if screen_width > 500 else 300,
                                height=60 if screen_width > 500 else 50,
                                bgcolor=BUTTON_COLORS['مصالح المديرية'],
                                on_click=lambda _: page.go("/direction"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(height=10),
                            create_elevated_button(
                                'أطر التفتيش والتوجيه',
                                width=360 if screen_width > 500 else 300,
                                height=60 if screen_width > 500 else 50,
                                bgcolor=BUTTON_COLORS['أطر التفتيش والتوجيه'],
                                on_click=lambda _: page.go("/inspector"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(height=10),
                            create_elevated_button(
                                'التعليم الإبتدائي',
                                width=360 if screen_width > 500 else 300,
                                height=60 if screen_width > 500 else 50,
                                bgcolor=BUTTON_COLORS['التعليم الإبتدائي'],
                                on_click=lambda _: page.go("/primaire"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(height=10),
                            create_elevated_button(
                                "الثانوي الإعدادي",
                                width=360 if screen_width > 500 else 300,
                                height=60 if screen_width > 500 else 50,
                                bgcolor=BUTTON_COLORS['الثانوي الإعدادي'],
                                on_click=lambda _: page.go("/college"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(height=10),
                            create_elevated_button(
                                'الثانوي التأهيلي',
                                width=360 if screen_width > 500 else 300,
                                height=60 if screen_width > 500 else 50,
                                bgcolor=BUTTON_COLORS['الثانوي التأهيلي'],
                                on_click=lambda _: page.go("/lycee"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(height=10),
                            # Bouton de mise à jour
                            update_container,
                        ],
                        alignment=MainAxisAlignment.START,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment='center',
                vertical_alignment='center',
                bgcolor=colors.LIGHT_BLUE_50
            )

            # Définir la couleur de fond de la vue
            view.bgcolor = colors.LIGHT_BLUE_50  # Couleur de fond neutre
            view.horizontal_alignment = 'center'
            view.vertical_alignment = 'center'

            page.views.append(view)
# Direction & Services 
        elif page.route == "/direction":
            screen_width = page.window.width
            text_size = get_text_size(screen_width)
            # Définir la couleur des boutons
            DIRECTOR_BUTTON_COLOR = colors.GREEN_600  # Couleur unique pour "المدير الإقليمي"
            SUB_BUTTON_COLOR1 = colors.GREEN_400      # Nuance pour "مكتب الضبط"
            SUB_BUTTON_COLOR2 = colors.GREEN_400      # Nuance pour "الكتابة الخاصة"
            # Autres couleurs pour les autres boutons (chaque bouton aura une couleur unique)
            OTHER_BUTTON_COLORS = [
                colors.RED_600,          # الشؤون التربوية
                colors.ORANGE_600,       # الموارد البشرية
                colors.CYAN_600,         # البناءات والتجهيز والمتلكات
                colors.PURPLE_600,         # الشؤون القانونية والتواصل
                colors.LIME_600,         # الشؤون الإدارية والمالية
                colors.PINK_600,         # المركز الإقليمي للإمتحانات
                colors.INDIGO_600,       # التخطيط والخريطة المدرسية
                colors.TEAL_600,         # تأطير المؤسسات والتوجيه
                colors.YELLOW_600,]      # المركز الإقليمي لمنظومة الإعلام
            # Vérifier qu'il y a suffisamment de couleurs pour les boutons
            if len(OTHER_BUTTON_COLORS) < 9:
                logging.error("Pas assez de couleurs définies dans OTHER_BUTTON_COLORS.")
                return
            view = View("/direction", [
                # AppBar avec retour automatique
                AppBar(
                    bgcolor=colors.BLUE_600,
                    title=Text("مصالح المديرية", color='white', size=24,),
                    center_title=True,
                    toolbar_height=55
                ),
                Container(
                    padding=padding.all(2),
                    alignment=alignment.center,
                    content=Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        controls=[
                            # Bouton "المدير الإقليمي" avec largeur augmentée
                            create_elevated_button(
                                "المدير الإقليمي",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=DIRECTOR_BUTTON_COLOR,
                                on_click=lambda _: page.go("/direction/directeur"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                alignment=alignment.center,
                                content=Divider(height=20, thickness=3, color=colors.BLACK),
                            ),
                            # Row contenant les boutons "مكتب الضبط" et "الكتابة الخاصة" avec largeur augmentée
                            Row(
                                controls=[
                                    create_elevated_button(
                                        "مكتب الضبط",
                                        width=190 if screen_width > 500 else 160,  # Augmentation de la largeur
                                        height=55 if screen_width > 500 else 45,
                                        bgcolor=SUB_BUTTON_COLOR1,
                                        on_click=lambda _: page.go("/direction/ordrebureau"),
                                        text_color=colors.WHITE,
                                        text_size=22 if screen_width > 500 else 18
                                    ),
                                    create_elevated_button(
                                        "الكتابة الخاصة",
                                        width=190 if screen_width > 500 else 160,  # Augmentation de la largeur
                                        height=55 if screen_width > 500 else 45,
                                        bgcolor=SUB_BUTTON_COLOR2,
                                        on_click=lambda _: page.go("/direction/secretaire"),
                                        text_color=colors.WHITE,
                                        text_size=22 if screen_width > 500 else 18
                                    )
                                ],
                                alignment=MainAxisAlignment.CENTER,
                                spacing=5,
                            ),
                            # Row contenant les boutons "الشؤون التربوية" et "الموارد البشرية" avec largeur augmentée
                            Row(
                                controls=[
                                    create_elevated_button(
                                        "الشؤون التربوية",
                                        width=190 if screen_width > 500 else 160,  # Augmentation de la largeur
                                        height=55 if screen_width > 500 else 45,
                                        bgcolor=OTHER_BUTTON_COLORS[0],
                                        on_click=lambda _: page.go("/direction/dae"),
                                        text_color=colors.WHITE,
                                        text_size=22 if screen_width > 500 else 18
                                    ),
                                    create_elevated_button(
                                        "الموارد البشرية",
                                        width=190 if screen_width > 500 else 160,  # Augmentation de la largeur
                                        height=55 if screen_width > 500 else 45,
                                        bgcolor=OTHER_BUTTON_COLORS[1],
                                        on_click=lambda _: page.go("/direction/grh"),
                                        text_color=colors.WHITE,
                                        text_size=22 if screen_width > 500 else 18
                                    )
                                ],
                                alignment=MainAxisAlignment.CENTER,
                                spacing=5,
                            ),
                            # Boutons supplémentaires avec différentes couleurs et largeur augmentée
                            create_elevated_button(
                                "البناءات والتجهيز والمتلكات",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[2],
                                on_click=lambda _: page.go("/direction/construction"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            create_elevated_button(
                                "الشؤون القانونية والتواصل",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[3],
                                on_click=lambda _: page.go("/direction/communication"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            create_elevated_button(
                                "الشؤون الإدارية والمالية",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[4],
                                on_click=lambda _: page.go("/direction/finance"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            create_elevated_button(
                                "المركز الإقليمي للإمتحانات",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[5],
                                on_click=lambda _: page.go("/direction/exam"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            create_elevated_button(
                                "التخطيط والخريطة المدرسية",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[6],
                                on_click=lambda _: page.go("/direction/planification"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            create_elevated_button(
                                "تأطير المؤسسات والتوجيه",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[7],
                                on_click=lambda _: page.go("/direction/encadrement"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            create_elevated_button(
                                "المركز الإقليمي لمنظومة الإعلام",
                                width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                height=60 if screen_width > 500 else 50,
                                bgcolor=OTHER_BUTTON_COLORS[8],
                                on_click=lambda _: page.go("/direction/information"),
                                text_color=colors.WHITE,
                                text_size=text_size
                            ),
                            Container(height=5),
                        ],
                        spacing=8
                    )
                )
            ])
            view.bgcolor = '#f0f0f0'  # Couleur de fond neutre
            view.horizontal_alignment = 'center'
            view.vertical_alignment = 'center'
            page.views.append(view)

        elif page.route == "/direction/directeur":
            show_directeur_view(page)



        elif page.route == "/direction/ordrebureau":
            service_data = load_contacts_by_service("ordrebureau")
            create_service_view(
                page=page,
                route="/direction/ordrebureau",
                service_data=service_data,
                title="مكتب الضبط",
                view_bgcolor=colors.LIGHT_BLUE_50,
                button_bgcolor=colors.GREEN_400
            )
        elif page.route == "/direction/secretaire":
            service_data = load_contacts_by_service("secretaire")
            create_service_view(
                page=page,
                route="/direction/secretaire",
                service_data=service_data,
                title="الكتابة الخاصة",
                view_bgcolor=colors.LIGHT_BLUE_50,
                button_bgcolor=colors.GREEN_400
            )
        elif page.route == "/direction/dae":
            service_data = load_contacts_by_service("dae")
            create_service_view(
                page=page,
                route="/direction/dae",
                service_data=service_data,
                title="مصلحة الشؤون التربوية",
                view_bgcolor=colors.RED_50,
                button_bgcolor=colors.RED_600
            )
        elif page.route == "/direction/grh":
            service_data = load_contacts_by_service("grh")
            create_service_view(
                page=page,
                route="/direction/grh",
                service_data=service_data,
                title="مصلحة الموارد البشرية",
                view_bgcolor=colors.DEEP_ORANGE_50,
                button_bgcolor=colors.ORANGE_600
            )
        elif page.route == "/direction/construction":
            service_data = load_contacts_by_service("construction")
            create_service_view(
                page=page,
                route="/direction/construction",
                service_data=service_data,
                title="البناءات والتجهيز والمتلكات",
                view_bgcolor=colors.CYAN_50,
                button_bgcolor=colors.CYAN_600
            )
        elif page.route == "/direction/communication":
            service_data = load_contacts_by_service("communication")
            create_service_view(
                page=page,
                route="/direction/communication",
                service_data=service_data,
                title="الشؤون القانونية والتواصل",
                view_bgcolor=colors.PURPLE_50,
                button_bgcolor=colors.PURPLE_600
            )
        elif page.route == "/direction/finance":
            service_data = load_contacts_by_service("finance")
            create_service_view(
                page=page,
                route="/direction/finance",
                service_data=service_data,
                title="الشؤون الإدارية والمالية",
                view_bgcolor=colors.LIME_50,
                button_bgcolor=colors.LIME_600
            )
        elif page.route == "/direction/exam":
            service_data = load_contacts_by_service("exam")
            create_service_view(
                page=page,
                route="/direction/exam",
                service_data=service_data,
                title="المركز الإقليمي للإمتحانات",
                view_bgcolor=colors.PINK_50,
                button_bgcolor=colors.PINK_600
            )
        elif page.route == "/direction/planification":
            service_data = load_contacts_by_service("planification")
            create_service_view(
                page=page,
                route="/direction/planification",
                service_data=service_data,
                title="التخطيط والخريطة المدرسية",
                view_bgcolor=colors.INDIGO_50,
                button_bgcolor=colors.INDIGO_600
            )
        elif page.route == "/direction/encadrement":
            service_data = load_contacts_by_service("encadrement")
            create_service_view(
                page=page,
                route="/direction/encadrement",
                service_data=service_data,
                title="تأطير المؤسسات والتوجيه",
                view_bgcolor=colors.TEAL_50,
                button_bgcolor=colors.TEAL_600
            )
        elif page.route == "/direction/information":
            service_data = load_contacts_by_service("information")
            create_service_view(
                page=page,
                route="/direction/information",
                service_data=service_data,
                title="المركز الإقليمي لمنظومة الإعلام",
                view_bgcolor=colors.YELLOW_50,
                button_bgcolor=colors.YELLOW_600
            )

# Les inspectors Section---------------------------
        elif page.route == "/inspector":
            screen_width = page.window.width
            text_size = get_text_size(screen_width)  # Assurez-vous que cette fonction est définie

            # Liste des couleurs uniques pour les boutons
            INSPECTOR_BUTTON_COLORS = [
                colors.BLACK45,          # مفتشي السلك الابتدائي
                colors.DEEP_PURPLE_ACCENT_100,    # مفتشي السلك التأهيلي
                colors.DEEP_ORANGE,    # مفتشي الشؤون المالية
                colors.TEAL,           # مفتشي التخطيط التربوي
                colors.GREEN,          # مفتشي التوجيه التربوي
                colors.BLUE,           # أطر التوجيه التربوي
            ]

            # Vérifier qu'il y a suffisamment de couleurs pour les boutons
            if len(INSPECTOR_BUTTON_COLORS) < 6:
                logging.error("Pas assez de couleurs définies dans INSPECTOR_BUTTON_COLORS.")
                return

            view = View(
                "/inspector",
                [
                    # AppBar avec retour automatique
                    AppBar(
                        bgcolor=colors.BLUE,
                        title=Text(
                            "المفتشوون وأطر التوجيه ",
                            rtl=True,
                            color='white',
                            size=24 if screen_width > 500 else 18  # Taille de texte responsive
                        ),
                        center_title=True,
                        automatically_imply_leading=True,),
                    Container(height=20),
                    # Contenu principal avec Column
                    Container(
                        padding=padding.all(16),
                        alignment=alignment.center,
                        content=Column(
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                # Bouton "مفتشي السلك الابتدائي"
                                create_elevated_button(
                                    content="مفتشو السلك الابتدائي",
                                    width=380 if screen_width > 500 else 320,  # Augmentation de la largeur
                                    height=60 if screen_width > 500 else 50,
                                    bgcolor=INSPECTOR_BUTTON_COLORS[0],  # Couleur unique
                                    on_click=lambda _: page.go("/inspector/primaire"),
                                    text_color=colors.WHITE,
                                    text_size=24 if screen_width > 500 else 18  # Taille de texte responsive
                                ),
                                Container(height=10),

                                # Bouton "مفتشي السلك التأهيلي"
                                create_elevated_button(
                                    content="مفتشو السلك التأهيلي",
                                    width=380 if screen_width > 500 else 320,
                                    height=60 if screen_width > 500 else 50,
                                    bgcolor=INSPECTOR_BUTTON_COLORS[1],  # Couleur unique
                                    on_click=lambda _: page.go("/inspector/secondaire"),
                                    text_color=colors.WHITE,
                                    text_size=24 if screen_width > 500 else 18
                                ),
                                Container(height=10),

                                # Bouton "مفتشي الشؤون المالية"
                                create_elevated_button(
                                    content="مفتشو الشؤون المالية",
                                    width=380 if screen_width > 500 else 320,
                                    height=60 if screen_width > 500 else 50,
                                    bgcolor=INSPECTOR_BUTTON_COLORS[2],  # Couleur unique
                                    on_click=lambda _: page.go("/inspector/finance"),
                                    text_color=colors.WHITE,
                                    text_size=24 if screen_width > 500 else 18
                                ),
                                Container(height=10),

                                # Bouton "مفتشي التخطيط التربوي"
                                create_elevated_button(
                                    content="مفتشو التخطيط التربوي",
                                    width=380 if screen_width > 500 else 320,
                                    height=60 if screen_width > 500 else 50,
                                    bgcolor=INSPECTOR_BUTTON_COLORS[3],  # Couleur unique
                                    on_click=lambda _: page.go("/inspector/planification"),
                                    text_color=colors.WHITE,
                                    text_size=24 if screen_width > 500 else 18
                                ),
                                Container(height=10),

                                # Bouton "مفتشي التوجيه التربوي"
                                create_elevated_button(
                                    content="مفتشو التوجيه التربوي",
                                    width=380 if screen_width > 500 else 320,
                                    height=60 if screen_width > 500 else 50,
                                    bgcolor=INSPECTOR_BUTTON_COLORS[4],  # Couleur unique
                                    on_click=lambda _: page.go("/inspector/orientation"),
                                    text_color=colors.WHITE,
                                    text_size=24 if screen_width > 500 else 18
                                ),
                                Container(height=10),

                                # Bouton "أطر التوجيه التربوي"
                                create_elevated_button(
                                    content="مستشارو التوجيه التربوي",
                                    width=380 if screen_width > 500 else 320,
                                    height=60 if screen_width > 500 else 50,
                                    bgcolor=INSPECTOR_BUTTON_COLORS[5],  # Couleur unique
                                    on_click=lambda _: page.go("/inspector/conseiller"),
                                    text_color=colors.WHITE,
                                    text_size=24 if screen_width > 500 else 18
                                ),
                                Container(height=10),
                            ],
                            spacing=10  # Espacement entre les boutons
                        )
                    )
                ],
                scroll='auto'  # Ajout de la fonctionnalité de défilement si le contenu dépasse
            )

            # Définir une couleur de fond cohérente pour la page
            view.bgcolor = colors.LIGHT_BLUE_50  # Exemple de couleur neutre, ajustez selon vos besoins
            view.horizontal_alignment = 'center'
            view.vertical_alignment = 'center'
            page.views.append(view)
            logging.info(len(page.views))
            logging.info(page.views[-1])

    
        elif page.route == "/inspector/secondaire":
            inspectors = load_inspectors_by_cycle("secondaire")
            create_inspector_view(
                page=page,
                route="/inspector/secondaire",
                inspectors_data=inspectors,
                title="مفتشو السلك التأهيلي",
                view_bgcolor=colors.DEEP_PURPLE_50,
                button_bgcolor=colors.DEEP_PURPLE_100  # Couleur plus foncée pour le bouton
            )
        elif page.route == "/inspector/primaire":
            inspectors = load_inspectors_by_cycle("primaire")
            create_inspector_view(
                page=page,
                route="/inspector/primaire",
                inspectors_data=inspectors,
                title="مفتشو السلك الابتدائي",
                view_bgcolor=colors.GREY_300,
                button_bgcolor=colors.GREY_400  # Une couleur légèrement plus foncée pour le bouton
            )
        elif page.route == "/inspector/finance":
            inspectors = load_inspectors_by_cycle("finance")
            create_inspector_view(
                page=page,
                route="/inspector/finance",
                inspectors_data=inspectors,
                title="مفتشو الشؤون المالية",
                view_bgcolor=colors.DEEP_ORANGE_50,
                button_bgcolor=colors.DEEP_ORANGE_100
            )
        elif page.route == "/inspector/planification":
            inspectors = load_inspectors_by_cycle("planification")
            create_inspector_view(
                page=page,
                route="/inspector/planification",
                inspectors_data=inspectors,
                title="مفتشو التخطيط التربوي",
                view_bgcolor=colors.TEAL_50,
                button_bgcolor=colors.TEAL_100
            )
        elif page.route == "/inspector/orientation":
            inspectors = load_inspectors_by_cycle("orientation")
            create_inspector_view(
                page=page,
                route="/inspector/orientation",
                inspectors_data=inspectors,
                title="مفتشو التوجيه التربوي",
                view_bgcolor=colors.LIGHT_GREEN_300,
                button_bgcolor=colors.LIGHT_GREEN_400
            )
        elif page.route == "/inspector/conseiller":
            inspectors = load_inspectors_by_cycle("conseiller")
            create_inspector_view(
                page=page,
                route="/inspector/conseiller",
                inspectors_data=inspectors,
                title="مستشارو التوجيه التربوي",
                view_bgcolor=colors.LIGHT_BLUE_ACCENT_100,
                button_bgcolor=colors.LIGHT_BLUE_300
            )
# Section des Cycles Scolaire
        elif page.route == "/primaire":
            show_school_contacts(
                sheet_name="primaire",
                icon_name=icons.SCHOOL,
                icon_color=colors.GREY,
                view_title="Établissements Primaires",
                view_bgcolor='#ffd966'
            )
        elif page.route == "/college":
            show_school_contacts(
                sheet_name="college",
                icon_name=icons.HOUSE,
                icon_color=colors.BLUE_GREY,
                view_title="Établissements Collégiaux",
                view_bgcolor='#e0f7fa'
            )
        elif page.route == "/lycee":
            show_school_contacts(
                sheet_name="lycee",
                icon_name=icons.APARTMENT,
                icon_color=colors.INDIGO,
                view_title="Établissements Lycéens",
                view_bgcolor='#e8eaf6'
            )
        page.update()
    def view_pop(e):
        logging.info(f"View pop: {e.view}")
        if len(page.views) > 1:  # S'il y a plus d'une vue, on retourne en arrière
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
    route_change(None)
app(target=main,assets_dir='assets/')
