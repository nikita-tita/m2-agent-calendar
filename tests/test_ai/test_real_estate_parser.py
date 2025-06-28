"""
Тесты для парсера недвижимости
"""

import pytest
from app.ai.nlp.real_estate_parser import RealEstateParser, PropertyInfo


class TestRealEstateParser:
    """Тесты для RealEstateParser"""
    
    @pytest.fixture
    def parser(self):
        """Создает экземпляр парсера для тестирования"""
        return RealEstateParser()
    
    def test_parse_apartment_text(self, parser):
        """Тест парсинга текста о квартире"""
        text = "Продается квартира 2 комнаты 50 кв.м за 5 млн рублей, 5 этаж из 9"
        
        result = parser.parse_text(text)
        
        assert result.property_type == "квартира"
        assert result.rooms == 2
        assert result.area == 50.0
        assert result.price == 5000000
        assert result.floor == 5
        assert result.total_floors == 9
        assert result.confidence > 0.5
    
    def test_parse_house_text(self, parser):
        """Тест парсинга текста о доме"""
        text = "Продается дом 150 кв.м за 15 млн рублей, 3 спальни"
        
        result = parser.parse_text(text)
        
        assert result.property_type == "дом"
        assert result.area == 150.0
        assert result.price == 15000000
        assert result.rooms == 3
        assert result.confidence > 0.5
    
    def test_parse_commercial_text(self, parser):
        """Тест парсинга текста о коммерческой недвижимости"""
        text = "Сдается офис 80 кв.м за 100 тыс рублей в месяц"
        
        result = parser.parse_text(text)
        
        assert result.property_type == "коммерческая"
        assert result.area == 80.0
        assert result.price == 100000
        assert result.confidence > 0.3
    
    def test_parse_studio_text(self, parser):
        """Тест парсинга текста о студии"""
        text = "Продается студия 30 кв.м за 3 млн рублей"
        
        result = parser.parse_text(text)
        
        assert result.property_type == "квартира"
        assert result.rooms == 0  # Студия = 0 комнат
        assert result.area == 30.0
        assert result.price == 3000000
        assert result.confidence > 0.5
    
    def test_parse_price_variations(self, parser):
        """Тест парсинга различных форматов цены"""
        test_cases = [
            ("5 млн рублей", 5000000),
            ("5000 тыс рублей", 5000000),
            ("5 000 000 руб", 5000000),
            ("5,000,000 рублей", 5000000),
            ("5.5 млн", 5500000),
            ("100 тыс", 100000),
        ]
        
        for text, expected_price in test_cases:
            result = parser.parse_text(f"Квартира за {text}")
            assert result.price == expected_price, f"Failed for text: {text}"
    
    def test_parse_area_variations(self, parser):
        """Тест парсинга различных форматов площади"""
        test_cases = [
            ("50 кв.м", 50.0),
            ("50 м²", 50.0),
            ("50 кв м", 50.0),
            ("50.5 кв.м", 50.5),
            ("50,5 кв.м", 50.5),
        ]
        
        for text, expected_area in test_cases:
            result = parser.parse_text(f"Квартира {text}")
            assert result.area == expected_area, f"Failed for text: {text}"
    
    def test_parse_rooms_variations(self, parser):
        """Тест парсинга различных форматов количества комнат"""
        test_cases = [
            ("2 комнаты", 2),
            ("2 комн", 2),
            ("двухкомнатная", 2),
            ("двушка", 2),
            ("3 спальни", 3),
            ("односпальная", 1),
        ]
        
        for text, expected_rooms in test_cases:
            result = parser.parse_text(f"Квартира {text}")
            assert result.rooms == expected_rooms, f"Failed for text: {text}"
    
    def test_parse_floor_variations(self, parser):
        """Тест парсинга различных форматов этажа"""
        test_cases = [
            ("5 этаж", {"floor": 5}),
            ("5/9", {"floor": 5, "total_floors": 9}),
            ("этаж 3", {"floor": 3}),
            ("3 этаж из 12", {"floor": 3, "total_floors": 12}),
        ]
        
        for text, expected_floor in test_cases.items():
            result = parser.parse_text(f"Квартира {text}")
            if "floor" in expected_floor:
                assert result.floor == expected_floor["floor"], f"Failed for text: {text}"
            if "total_floors" in expected_floor:
                assert result.total_floors == expected_floor["total_floors"], f"Failed for text: {text}"
    
    def test_parse_address(self, parser):
        """Тест парсинга адреса"""
        test_cases = [
            ("ул. Ленина 10", "Ленина 10"),
            ("пр. Мира 25", "Мира 25"),
            ("район Центральный", "Центральный"),
            ("м. Пушкинская", "Пушкинская"),
        ]
        
        for text, expected_address in test_cases:
            result = parser.parse_text(f"Квартира на {text}")
            assert result.address == expected_address, f"Failed for text: {text}"
    
    def test_parse_contact_info(self, parser):
        """Тест парсинга контактной информации"""
        test_cases = [
            ("+7 (999) 123-45-67", "+7 (999) 123-45-67"),
            ("8 999 123 45 67", "8 999 123 45 67"),
            ("test@example.com", "test@example.com"),
            ("тел: 123-45-67", "123-45-67"),
        ]
        
        for text, expected_contact in test_cases:
            result = parser.parse_text(f"Квартира. Контакт: {text}")
            assert result.contact == expected_contact, f"Failed for text: {text}"
    
    def test_parse_features(self, parser):
        """Тест парсинга особенностей недвижимости"""
        text = "Квартира с ремонтом, мебелью, балконом, парковкой"
        
        result = parser.parse_text(text)
        
        expected_features = ["ремонт", "мебель", "балкон", "парковка"]
        for feature in expected_features:
            assert feature in result.features
    
    def test_parse_renovation(self, parser):
        """Тест парсинга типа ремонта"""
        test_cases = [
            ("евроремонт", "евроремонт"),
            ("косметический ремонт", "косметический"),
            ("капитальный ремонт", "капитальный"),
            ("требует ремонта", "требует ремонта"),
        ]
        
        for text, expected_renovation in test_cases:
            result = parser.parse_text(f"Квартира с {text}")
            assert result.renovation == expected_renovation, f"Failed for text: {text}"
    
    def test_parse_year_built(self, parser):
        """Тест парсинга года постройки"""
        text = "Квартира в доме 2010 года постройки"
        
        result = parser.parse_text(text)
        
        assert result.year_built == 2010
    
    def test_parse_metro(self, parser):
        """Тест парсинга информации о метро"""
        text = "Квартира рядом с м. Пушкинская"
        
        result = parser.parse_text(text)
        
        assert result.metro == "Пушкинская"
    
    def test_parse_district(self, parser):
        """Тест парсинга района"""
        text = "Квартира в районе Центральный"
        
        result = parser.parse_text(text)
        
        assert result.district == "Центральный"
    
    def test_parse_complex_text(self, parser):
        """Тест парсинга сложного текста"""
        text = """
        Продается двухкомнатная квартира 65 кв.м за 7.5 млн рублей.
        Адрес: ул. Ленина 15, 5 этаж из 9, район Центральный.
        Рядом м. Пушкинская. Евроремонт, мебель, техника, балкон.
        Дом 2015 года постройки. Контакт: +7 (999) 123-45-67
        """
        
        result = parser.parse_text(text)
        
        assert result.property_type == "квартира"
        assert result.rooms == 2
        assert result.area == 65.0
        assert result.price == 7500000
        assert result.floor == 5
        assert result.total_floors == 9
        assert result.address == "Ленина 15"
        assert result.district == "Центральный"
        assert result.metro == "Пушкинская"
        assert result.renovation == "евроремонт"
        assert result.year_built == 2015
        assert result.contact == "+7 (999) 123-45-67"
        assert "мебель" in result.features
        assert "техника" in result.features
        assert "балкон" in result.features
        assert result.confidence > 0.7
    
    def test_parse_empty_text(self, parser):
        """Тест парсинга пустого текста"""
        result = parser.parse_text("")
        
        assert result.property_type is None
        assert result.price is None
        assert result.area is None
        assert result.confidence == 0.0
    
    def test_parse_unrelated_text(self, parser):
        """Тест парсинга текста, не связанного с недвижимостью"""
        text = "Сегодня хорошая погода для прогулки в парке"
        
        result = parser.parse_text(text)
        
        assert result.property_type is None
        assert result.price is None
        assert result.area is None
        assert result.confidence < 0.3
    
    def test_validate_property_info(self, parser):
        """Тест валидации информации о недвижимости"""
        # Валидная информация
        valid_info = PropertyInfo(
            property_type="квартира",
            price=5000000,
            area=50.0,
            rooms=2
        )
        
        validation = parser.validate_property_info(valid_info)
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
        
        # Невалидная информация
        invalid_info = PropertyInfo(
            price=5000000,
            area=50.0,
            rooms=2
            # Отсутствует property_type
        )
        
        validation = parser.validate_property_info(invalid_info)
        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0
        
        # Информация с предупреждениями
        warning_info = PropertyInfo(
            property_type="квартира",
            price=50000,  # Подозрительно низкая цена
            area=2000,    # Подозрительно большая площадь
            rooms=15      # Подозрительно много комнат
        )
        
        validation = parser.validate_property_info(warning_info)
        assert validation["is_valid"] is True
        assert len(validation["warnings"]) > 0
    
    def test_confidence_calculation(self, parser):
        """Тест вычисления уверенности"""
        # Полная информация
        full_info = PropertyInfo(
            property_type="квартира",
            price=5000000,
            area=50.0,
            rooms=2,
            address="ул. Ленина 10",
            floor=5,
            contact="+7 999 123-45-67",
            features=["ремонт", "мебель"]
        )
        
        confidence = parser._calculate_confidence(full_info)
        assert confidence > 0.8
        
        # Минимальная информация
        minimal_info = PropertyInfo(
            property_type="квартира"
        )
        
        confidence = parser._calculate_confidence(minimal_info)
        assert confidence < 0.3 