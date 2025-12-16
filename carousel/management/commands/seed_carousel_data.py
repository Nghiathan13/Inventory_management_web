from django.core.management.base import BaseCommand
from carousel.models import Carousel, Shelf, Tray

class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu kệ xoay: Xóa cũ và tạo mới (8 Kệ x 2 Tầng).'

    def handle(self, *args, **kwargs):
        if Carousel.objects.exists():
            self.stdout.write(self.style.WARNING('Đang xóa dữ liệu kệ xoay cũ...'))
            Carousel.objects.all().delete()

        self.stdout.write('Bắt đầu khởi tạo dữ liệu mới...')

        try:
            main_carousel = Carousel.objects.create(name="Nhà Thuốc Adoo")
            
            # --- THAY ĐỔI: Dùng số thay vì chữ cái ---
            # Tạo 8 kệ, đặt tên là "1", "2", ..., "8"
            shelf_names = [str(i) for i in range(1, 9)]
            
            shelves_created = 0
            trays_created = 0

            for name in shelf_names:
                shelf = Shelf.objects.create(carousel=main_carousel, name=name)
                shelves_created += 1
                
                # Tạo 2 tầng cho mỗi kệ
                for level in range(1, 3): 
                    Tray.objects.create(shelf=shelf, level=level)
                    trays_created += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'Hoàn tất! Đã tạo: 1 Hệ thống, {shelves_created} Kệ (1-8), và {trays_created} Khay.'
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Đã có lỗi xảy ra: {e}'))