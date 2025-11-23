from django.core.management.base import BaseCommand
from carousel.models import Carousel, Shelf, Tray

class Command(BaseCommand):
    # Dòng trợ giúp sẽ hiển thị khi bạn chạy: python manage.py help seed_carousel_data
    help = 'Khởi tạo dữ liệu ban đầu cho hệ thống kệ xoay (carousel), bao gồm 8 kệ và 3 tầng mỗi kệ.'

    def handle(self, *args, **kwargs):
        """
        Hàm chính sẽ được thực thi khi lệnh được gọi.
        """
        # Kiểm tra xem dữ liệu đã tồn tại chưa để tránh tạo lại
        if Carousel.objects.exists():
            self.stdout.write(self.style.WARNING('Dữ liệu kệ xoay đã tồn tại. Bỏ qua việc khởi tạo.'))
            return

        self.stdout.write('Bắt đầu khởi tạo dữ liệu cho kệ xoay...')

        # Tạo hệ thống kệ xoay chính
        try:
            main_carousel = Carousel.objects.create(name="Nhà Thuốc Adoo")
            
            shelf_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            shelves_created = 0
            trays_created = 0

            # Vòng lặp để tạo kệ và các tầng
            for name in shelf_names:
                shelf = Shelf.objects.create(carousel=main_carousel, name=name)
                shelves_created += 1
                
                for level in range(1, 4):
                    Tray.objects.create(shelf=shelf, level=level)
                    trays_created += 1
            
            # self.stdout.write() là cách chuẩn để in ra thông báo trong management command
            self.stdout.write(self.style.SUCCESS(
                f'Hoàn tất! Đã tạo thành công 1 hệ thống, {shelves_created} kệ, và {trays_created} khay.'
            ))

        except Exception as e:
            # Báo lỗi nếu có vấn đề xảy ra
            self.stderr.write(self.style.ERROR(f'Đã có lỗi xảy ra trong quá trình khởi tạo: {e}'))