from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Inventory, InventoryTransaction, Staff, Branch
from datetime import datetime

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
def list_inventory():
    """List all inventory items with filtering"""
    # Get filter parameters
    category = request.args.get('category')
    status = request.args.get('status')  # low stock vs normal
    search = request.args.get('search', '')

    # Base query
    query = Inventory.query

    # Apply filters
    if category:
        query = query.filter_by(category=category)
    if status == 'low':
        query = query.filter(Inventory.quantity <= Inventory.minimum_quantity)
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Inventory.name.ilike(search),
                Inventory.description.ilike(search)
            )
        )

    items = query.order_by(Inventory.name).all()
    return render_template('inventory/list.html', items=items)

@bp.route('/add', methods=['GET', 'POST'])
def add_item():
    """Add a new inventory item"""
    if request.method == 'POST':
        try:
            item = Inventory(
                name=request.form['name'],
                category=request.form['category'],
                quantity=request.form.get('quantity', type=int) or 0,
                unit=request.form['unit'],
                minimum_quantity=request.form.get('minimum_quantity', type=int) or 1,
                branch_id=request.form['branch_id'],
                location=request.form.get('location'),
                description=request.form.get('description'),
                unit_price=request.form.get('unit_price', type=float),
                supplier_info=request.form.get('supplier_info')
            )
            
            db.session.add(item)
            db.session.commit()
            
            # Add initial stock transaction if quantity > 0
            if item.quantity > 0:
                transaction = InventoryTransaction(
                    inventory_id=item.id,
                    transaction_type='IN',
                    quantity=item.quantity,
                    reference='Initial Stock',
                    performed_by=request.form.get('staff_id'),
                    notes='Initial inventory addition'
                )
                db.session.add(transaction)
                db.session.commit()
            
            flash('Inventory item added successfully!', 'success')
            return redirect(url_for('inventory.view_item', item_id=item.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding inventory item: {str(e)}', 'error')

    # Get branches for the form
    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('inventory/add.html', branches=branches)

@bp.route('/<int:item_id>')
def view_item(item_id):
    """View inventory item details"""
    item = Inventory.query.get_or_404(item_id)
    
    # Get recent transactions
    recent_transactions = InventoryTransaction.query.filter_by(
        inventory_id=item_id
    ).order_by(InventoryTransaction.transaction_date.desc()).limit(10).all()
    
    return render_template('inventory/view.html',
                         item=item,
                         transactions=recent_transactions)

@bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    """Edit inventory item details"""
    item = Inventory.query.get_or_404(item_id)
    
    if request.method == 'POST':
        try:
            item.name = request.form['name']
            item.category = request.form['category']
            item.unit = request.form['unit']
            item.minimum_quantity = request.form.get('minimum_quantity', type=int) or 1
            item.location = request.form.get('location')
            item.description = request.form.get('description')
            item.unit_price = request.form.get('unit_price', type=float)
            item.supplier_info = request.form.get('supplier_info')
            
            db.session.commit()
            flash('Inventory item updated successfully!', 'success')
            return redirect(url_for('inventory.view_item', item_id=item_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory item: {str(e)}', 'error')

    # Get branches for the form
    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('inventory/edit.html', item=item, branches=branches)

@bp.route('/<int:item_id>/transaction', methods=['POST'])
def add_transaction(item_id):
    """Record an inventory transaction (stock in/out)"""
    item = Inventory.query.get_or_404(item_id)
    
    try:
        quantity = request.form.get('quantity', type=int)
        transaction_type = request.form['transaction_type']
        
        # Validate stock-out quantity
        if transaction_type == 'OUT' and quantity > item.quantity:
            flash('Insufficient stock!', 'error')
            return redirect(url_for('inventory.view_item', item_id=item_id))
        
        # Update item quantity
        if transaction_type == 'IN':
            item.quantity += quantity
        else:
            item.quantity -= quantity
        
        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=item_id,
            transaction_type=transaction_type,
            quantity=quantity,
            reference=request.form.get('reference'),
            performed_by=request.form.get('staff_id'),
            notes=request.form.get('notes')
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction recorded successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording transaction: {str(e)}', 'error')
        
    return redirect(url_for('inventory.view_item', item_id=item_id))

@bp.route('/low-stock')
def low_stock():
    """View items with low stock"""
    items = Inventory.query.filter(
        Inventory.quantity <= Inventory.minimum_quantity
    ).order_by(Inventory.quantity.asc()).all()
    
    return render_template('inventory/low_stock.html', items=items)
